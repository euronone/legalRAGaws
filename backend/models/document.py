from pydantic import BaseModel
from typing import Optional


class DocumentMetadata(BaseModel):
    source_file: str
    s3_key: str
    page_number: int
    chunk_index: int
    section_header: Optional[str] = None
    file_hash: str
    citation: str
    uploaded_at: str
    total_pages: int


class DocumentChunk(BaseModel):
    text: str
    metadata: DocumentMetadata
    embedding: Optional[list[float]] = None


class ProcessedFileRecord(BaseModel):
    file_hash: str
    filename: str
    s3_key: str
    processed_at: str
    status: str  # "processed", "failed"
    total_chunks: int = 0
    total_pages: int = 0


class UploadResponse(BaseModel):
    message: str
    filename: str
    s3_key: str
    is_duplicate: bool
    chunks_created: int = 0
