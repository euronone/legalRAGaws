from fastapi import APIRouter, UploadFile, File, HTTPException
from datetime import datetime, timezone

from backend.models.document import UploadResponse, ProcessedFileRecord
from backend.services.s3_service import upload_file_to_s3
from backend.services.dedup_middleware import check_duplicate
from backend.services.document_processor import process_document
from backend.services.embedding_service import generate_embedding
from backend.services.opensearch_service import (
    index_chunks_bulk,
    mark_file_processed,
)

router = APIRouter(prefix="/api", tags=["upload"])


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a legal document (PDF or DOCX)."""
    # Validate file type
    filename = file.filename or "unknown"
    if not filename.lower().endswith((".pdf", ".docx", ".doc")):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Only PDF and DOCX files are accepted.",
        )

    # Read file bytes
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file.")

    # Check for duplicates
    is_duplicate, file_hash = check_duplicate(file_bytes)
    if is_duplicate:
        return UploadResponse(
            message="File has already been processed. Skipping.",
            filename=filename,
            s3_key="",
            is_duplicate=True,
            chunks_created=0,
        )

    # Upload to S3
    s3_key = upload_file_to_s3(file_bytes, filename)
    uploaded_at = datetime.now(timezone.utc).isoformat()

    # Process document into chunks
    try:
        chunks = process_document(
            file_bytes=file_bytes,
            filename=filename,
            s3_key=s3_key,
            file_hash=file_hash,
            uploaded_at=uploaded_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Generate embeddings for each chunk
    for chunk in chunks:
        chunk.embedding = generate_embedding(chunk.text)

    # Store in OpenSearch (bulk with dedup by doc_id)
    index_chunks_bulk(chunks)

    # Mark file as processed
    record = ProcessedFileRecord(
        file_hash=file_hash,
        filename=filename,
        s3_key=s3_key,
        processed_at=uploaded_at,
        status="processed",
        total_chunks=len(chunks),
        total_pages=chunks[0].metadata.total_pages if chunks else 0,
    )
    mark_file_processed(record)

    return UploadResponse(
        message="Document uploaded and processed successfully.",
        filename=filename,
        s3_key=s3_key,
        is_duplicate=False,
        chunks_created=len(chunks),
    )
