from opensearchpy import OpenSearch, RequestsHttpConnection
from backend.config import settings
from backend.models.document import DocumentChunk, ProcessedFileRecord


def get_opensearch_client() -> OpenSearch:
    """Create OpenSearch client with basic auth."""
    return OpenSearch(
        hosts=[{"host": settings.OPENSEARCH_ENDPOINT, "port": 443}],
        http_auth=(settings.OPENSEARCH_MASTER_USER, settings.OPENSEARCH_MASTER_PASSWORD),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
    )


# --- Processed Files Tracking ---

def is_file_processed(file_hash: str) -> bool:
    """Check if a file with this hash has already been processed."""
    client = get_opensearch_client()
    query = {"query": {"term": {"file_hash": file_hash}}}

    try:
        response = client.search(index=settings.PROCESSED_FILES_INDEX, body=query)
        return response["hits"]["total"]["value"] > 0
    except Exception:
        return False


def mark_file_processed(record: ProcessedFileRecord):
    """Record that a file has been processed."""
    client = get_opensearch_client()
    client.index(
        index=settings.PROCESSED_FILES_INDEX,
        id=record.file_hash,
        body=record.model_dump(),
    )


# --- Document Chunk Operations ---

def chunk_exists(file_hash: str, chunk_index: int) -> bool:
    """Check if a specific chunk already exists in the index."""
    client = get_opensearch_client()
    doc_id = f"{file_hash}_{chunk_index}"
    try:
        client.get(index=settings.LEGAL_DOCS_INDEX, id=doc_id)
        return True
    except Exception:
        return False


def index_chunk(chunk: DocumentChunk):
    """Index a single document chunk into OpenSearch."""
    client = get_opensearch_client()
    doc_id = f"{chunk.metadata.file_hash}_{chunk.metadata.chunk_index}"

    body = {
        "embedding": chunk.embedding,
        "text": chunk.text,
        "source_file": chunk.metadata.source_file,
        "s3_key": chunk.metadata.s3_key,
        "page_number": chunk.metadata.page_number,
        "chunk_index": chunk.metadata.chunk_index,
        "section_header": chunk.metadata.section_header,
        "file_hash": chunk.metadata.file_hash,
        "citation": chunk.metadata.citation,
        "uploaded_at": chunk.metadata.uploaded_at,
        "total_pages": chunk.metadata.total_pages,
    }

    client.index(index=settings.LEGAL_DOCS_INDEX, id=doc_id, body=body)


def index_chunks_bulk(chunks: list[DocumentChunk]):
    """Bulk index document chunks with deduplication check."""
    client = get_opensearch_client()
    actions = []

    for chunk in chunks:
        doc_id = f"{chunk.metadata.file_hash}_{chunk.metadata.chunk_index}"

        actions.append({"index": {"_index": settings.LEGAL_DOCS_INDEX, "_id": doc_id}})
        actions.append({
            "embedding": chunk.embedding,
            "text": chunk.text,
            "source_file": chunk.metadata.source_file,
            "s3_key": chunk.metadata.s3_key,
            "page_number": chunk.metadata.page_number,
            "chunk_index": chunk.metadata.chunk_index,
            "section_header": chunk.metadata.section_header,
            "file_hash": chunk.metadata.file_hash,
            "citation": chunk.metadata.citation,
            "uploaded_at": chunk.metadata.uploaded_at,
            "total_pages": chunk.metadata.total_pages,
        })

    if actions:
        client.bulk(body=actions)
        # Force refresh to make documents searchable immediately
        client.indices.refresh(index=settings.LEGAL_DOCS_INDEX)


# --- Search Operations ---

def semantic_search(query_embedding: list[float], top_k: int = 5) -> list[dict]:
    """Perform k-NN vector similarity search."""
    client = get_opensearch_client()

    query = {
        "size": top_k,
        "query": {
            "knn": {
                "embedding": {
                    "vector": query_embedding,
                    "k": top_k,
                }
            }
        },
        "_source": {
            "excludes": ["embedding"]
        },
    }

    response = client.search(index=settings.LEGAL_DOCS_INDEX, body=query)

    results = []
    for hit in response["hits"]["hits"]:
        result = hit["_source"]
        result["score"] = hit["_score"]
        result["search_type"] = "semantic"
        results.append(result)

    return results


def keyword_search(query_text: str, top_k: int = 5) -> list[dict]:
    """Perform BM25 keyword search."""
    client = get_opensearch_client()

    query = {
        "size": top_k,
        "query": {
            "match": {
                "text": {
                    "query": query_text,
                    "operator": "or",
                }
            }
        },
        "_source": {
            "excludes": ["embedding"]
        },
    }

    response = client.search(index=settings.LEGAL_DOCS_INDEX, body=query)

    results = []
    for hit in response["hits"]["hits"]:
        result = hit["_source"]
        result["score"] = hit["_score"]
        result["search_type"] = "keyword"
        results.append(result)

    return results
