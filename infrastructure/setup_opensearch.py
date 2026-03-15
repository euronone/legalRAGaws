import boto3
import json
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config import settings


def create_opensearch_domain():
    """Create OpenSearch domain with k-NN plugin enabled."""
    client = boto3.client(
        "opensearch",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    domain_name = settings.OPENSEARCH_DOMAIN_NAME

    # Check if domain already exists
    try:
        response = client.describe_domain(DomainName=domain_name)
        endpoint = response["DomainStatus"].get("Endpoint") or response["DomainStatus"].get("Endpoints", {}).get("vpc", "")
        if endpoint:
            print(f"[OK] OpenSearch domain '{domain_name}' already exists.")
            print(f"     Endpoint: {endpoint}")
            return endpoint
        else:
            print(f"[..] OpenSearch domain '{domain_name}' exists but is still being created...")
    except client.exceptions.ResourceNotFoundException:
        pass

    # Ensure master password is set
    master_password = settings.OPENSEARCH_MASTER_PASSWORD
    if not master_password:
        print("[ERROR] OPENSEARCH_MASTER_PASSWORD is not set in .env")
        print("        Password must be at least 8 chars with uppercase, lowercase, number, and special char.")
        sys.exit(1)

    print(f"[..] Creating OpenSearch domain '{domain_name}'...")
    print("     This may take 15-20 minutes...")

    client.create_domain(
        DomainName=domain_name,
        EngineVersion="OpenSearch_2.11",
        ClusterConfig={
            "InstanceType": settings.OPENSEARCH_INSTANCE_TYPE,
            "InstanceCount": settings.OPENSEARCH_INSTANCE_COUNT,
            "DedicatedMasterEnabled": False,
            "ZoneAwarenessEnabled": False,
        },
        EBSOptions={
            "EBSEnabled": True,
            "VolumeType": "gp3",
            "VolumeSize": settings.OPENSEARCH_EBS_SIZE,
        },
        AccessPolicies=json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": "*"},
                    "Action": "es:*",
                    "Resource": f"arn:aws:es:{settings.AWS_REGION}:*:domain/{domain_name}/*",
                }
            ],
        }),
        EncryptionAtRestOptions={"Enabled": True},
        NodeToNodeEncryptionOptions={"Enabled": True},
        DomainEndpointOptions={
            "EnforceHTTPS": True,
            "TLSSecurityPolicy": "Policy-Min-TLS-1-2-2019-07",
        },
        AdvancedSecurityOptions={
            "Enabled": True,
            "InternalUserDatabaseEnabled": True,
            "MasterUserOptions": {
                "MasterUserName": settings.OPENSEARCH_MASTER_USER,
                "MasterUserPassword": master_password,
            },
        },
    )

    # Wait for domain to become active
    print("[..] Waiting for domain to become active...")
    while True:
        response = client.describe_domain(DomainName=domain_name)
        status = response["DomainStatus"]
        processing = status.get("Processing", True)
        endpoint = status.get("Endpoint", "")

        if not processing and endpoint:
            print(f"[OK] OpenSearch domain is active.")
            print(f"     Endpoint: {endpoint}")
            return endpoint

        print("     Still provisioning... (checking again in 30s)")
        time.sleep(30)


def create_indices(endpoint: str):
    """Create the legal_documents and processed_files indices."""
    from opensearchpy import OpenSearch, RequestsHttpConnection
    opensearch_client = OpenSearch(
        hosts=[{"host": endpoint, "port": 443}],
        http_auth=(settings.OPENSEARCH_MASTER_USER, settings.OPENSEARCH_MASTER_PASSWORD),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
    )

    # Legal documents index with k-NN
    legal_index_body = {
        "settings": {
            "index": {
                "knn": True,
                "number_of_shards": 1,
                "number_of_replicas": 0,
            }
        },
        "mappings": {
            "properties": {
                "embedding": {
                    "type": "knn_vector",
                    "dimension": settings.EMBEDDING_DIMENSION,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "nmslib",
                        "parameters": {
                            "ef_construction": 512,
                            "m": 16,
                        },
                    },
                },
                "text": {"type": "text", "analyzer": "standard"},
                "source_file": {"type": "keyword"},
                "s3_key": {"type": "keyword"},
                "page_number": {"type": "integer"},
                "chunk_index": {"type": "integer"},
                "section_header": {"type": "text"},
                "file_hash": {"type": "keyword"},
                "citation": {"type": "text"},
                "uploaded_at": {"type": "date"},
                "total_pages": {"type": "integer"},
            }
        },
    }

    # Processed files tracking index
    processed_index_body = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
        },
        "mappings": {
            "properties": {
                "file_hash": {"type": "keyword"},
                "filename": {"type": "keyword"},
                "s3_key": {"type": "keyword"},
                "processed_at": {"type": "date"},
                "status": {"type": "keyword"},
                "total_chunks": {"type": "integer"},
                "total_pages": {"type": "integer"},
            }
        },
    }

    for index_name, body in [
        (settings.LEGAL_DOCS_INDEX, legal_index_body),
        (settings.PROCESSED_FILES_INDEX, processed_index_body),
    ]:
        if not opensearch_client.indices.exists(index=index_name):
            opensearch_client.indices.create(index=index_name, body=body)
            print(f"[OK] Index '{index_name}' created.")
        else:
            print(f"[OK] Index '{index_name}' already exists.")


if __name__ == "__main__":
    endpoint = create_opensearch_domain()
    if endpoint:
        create_indices(endpoint)
