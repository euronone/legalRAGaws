import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # AWS Credentials
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")

    # S3
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "legal-rag-documents")

    # OpenSearch
    OPENSEARCH_DOMAIN_NAME: str = os.getenv("OPENSEARCH_DOMAIN_NAME", "legal-rag-search")
    OPENSEARCH_ENDPOINT: str = os.getenv("OPENSEARCH_ENDPOINT", "")
    OPENSEARCH_MASTER_USER: str = os.getenv("OPENSEARCH_MASTER_USER", "admin")
    OPENSEARCH_MASTER_PASSWORD: str = os.getenv("OPENSEARCH_MASTER_PASSWORD", "")
    OPENSEARCH_INSTANCE_TYPE: str = os.getenv("OPENSEARCH_INSTANCE_TYPE", "t3.small.search")
    OPENSEARCH_INSTANCE_COUNT: int = int(os.getenv("OPENSEARCH_INSTANCE_COUNT", "1"))
    OPENSEARCH_EBS_SIZE: int = int(os.getenv("OPENSEARCH_EBS_SIZE", "20"))

    # Bedrock
    BEDROCK_EMBEDDING_MODEL_ID: str = os.getenv("BEDROCK_EMBEDDING_MODEL_ID", "amazon.titan-embed-text-v1")
    BEDROCK_LLM_MODEL_ID: str = os.getenv("BEDROCK_LLM_MODEL_ID", "amazon.titan-text-premier-v1:0")

    # OpenSearch Index Names
    LEGAL_DOCS_INDEX: str = "legal_documents"
    PROCESSED_FILES_INDEX: str = "processed_files"

    # Chunking
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200

    # Retrieval
    TOP_K: int = 5
    RERANK_ALPHA: float = 0.7  # Weight for semantic vs keyword (0.7 = 70% semantic)

    # Embedding
    EMBEDDING_DIMENSION: int = 1536  # Titan Embed v1 output dimension


settings = Settings()
