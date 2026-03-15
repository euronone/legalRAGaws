import io
from typing import Optional
from backend.config import settings
from backend.models.document import DocumentMetadata, DocumentChunk


def extract_text_from_pdf(file_bytes: bytes) -> list[dict]:
    """Extract text from PDF, returning list of {page_number, text}."""
    from PyPDF2 import PdfReader

    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append({"page_number": i + 1, "text": text.strip()})
    return pages


def extract_text_from_docx(file_bytes: bytes) -> list[dict]:
    """Extract text from DOCX, returning list of {page_number, text}."""
    from docx import Document

    doc = Document(io.BytesIO(file_bytes))
    full_text = []
    current_section = ""

    for para in doc.paragraphs:
        if para.text.strip():
            current_section += para.text + "\n"

    # DOCX doesn't have native page numbers, treat as single page
    return [{"page_number": 1, "text": current_section.strip()}]


def extract_section_header(text: str) -> Optional[str]:
    """Try to extract a section header from the beginning of a chunk."""
    lines = text.strip().split("\n")
    if lines:
        first_line = lines[0].strip()
        # Heuristic: short lines that look like headers
        if len(first_line) < 100 and (
            first_line.isupper()
            or first_line.startswith("Section")
            or first_line.startswith("Article")
            or first_line.startswith("ARTICLE")
            or first_line[0].isdigit()
        ):
            return first_line
    return None


def chunk_text(text: str, chunk_size: int = None, overlap: int = None) -> list[str]:
    """Split text into overlapping chunks using recursive character splitting."""
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap or settings.CHUNK_OVERLAP

    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    # Recursive splitting by separators
    separators = ["\n\n", "\n", ". ", " "]
    chunks = []

    def split_recursive(text: str, separators: list[str]) -> list[str]:
        if len(text) <= chunk_size:
            return [text] if text.strip() else []

        sep = separators[0] if separators else " "
        remaining_seps = separators[1:] if len(separators) > 1 else []

        parts = text.split(sep)
        current_chunk = ""
        result = []

        for part in parts:
            test_chunk = current_chunk + sep + part if current_chunk else part
            if len(test_chunk) <= chunk_size:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    result.append(current_chunk)
                if len(part) > chunk_size and remaining_seps:
                    result.extend(split_recursive(part, remaining_seps))
                else:
                    current_chunk = part

        if current_chunk:
            result.append(current_chunk)

        return result

    raw_chunks = split_recursive(text, separators)

    # Apply overlap
    if overlap > 0 and len(raw_chunks) > 1:
        overlapped = [raw_chunks[0]]
        for i in range(1, len(raw_chunks)):
            prev = raw_chunks[i - 1]
            overlap_text = prev[-overlap:] if len(prev) > overlap else prev
            overlapped.append(overlap_text + raw_chunks[i])
        return overlapped

    return raw_chunks


def process_document(
    file_bytes: bytes,
    filename: str,
    s3_key: str,
    file_hash: str,
    uploaded_at: str,
) -> list[DocumentChunk]:
    """Process a document into chunks with metadata."""
    # Determine file type and extract text
    if filename.lower().endswith(".pdf"):
        pages = extract_text_from_pdf(file_bytes)
    elif filename.lower().endswith((".docx", ".doc")):
        pages = extract_text_from_docx(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {filename}")

    total_pages = len(pages)
    all_chunks = []
    chunk_index = 0

    for page_data in pages:
        page_num = page_data["page_number"]
        page_text = page_data["text"]

        if not page_text.strip():
            continue

        text_chunks = chunk_text(page_text)

        for chunk_text_content in text_chunks:
            if not chunk_text_content.strip():
                continue

            section_header = extract_section_header(chunk_text_content)
            citation = f"{filename}, Page {page_num}"
            if section_header:
                citation += f", {section_header}"

            metadata = DocumentMetadata(
                source_file=filename,
                s3_key=s3_key,
                page_number=page_num,
                chunk_index=chunk_index,
                section_header=section_header,
                file_hash=file_hash,
                citation=citation,
                uploaded_at=uploaded_at,
                total_pages=total_pages,
            )

            all_chunks.append(DocumentChunk(text=chunk_text_content, metadata=metadata))
            chunk_index += 1

    return all_chunks
