"""Tests for the document ingestion pipeline."""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.document_processor import chunk_text, extract_section_header
from backend.services.s3_service import compute_file_hash


def test_chunk_text_short():
    """Short text should return a single chunk."""
    text = "This is a short text."
    chunks = chunk_text(text, chunk_size=1000, overlap=200)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_chunk_text_long():
    """Long text should be split into multiple chunks."""
    text = "Word " * 500  # ~2500 chars
    chunks = chunk_text(text, chunk_size=500, overlap=100)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) > 0


def test_chunk_text_empty():
    """Empty text should return no chunks."""
    chunks = chunk_text("", chunk_size=1000, overlap=200)
    assert len(chunks) == 0


def test_compute_file_hash():
    """Same content should produce same hash."""
    content = b"test content"
    hash1 = compute_file_hash(content)
    hash2 = compute_file_hash(content)
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex digest


def test_compute_file_hash_different():
    """Different content should produce different hash."""
    hash1 = compute_file_hash(b"content A")
    hash2 = compute_file_hash(b"content B")
    assert hash1 != hash2


def test_extract_section_header():
    """Should extract header-like first lines."""
    text = "ARTICLE 1\nThis is the body of the article."
    header = extract_section_header(text)
    assert header == "ARTICLE 1"


def test_extract_section_header_none():
    """Long first lines should not be treated as headers."""
    text = "This is a very long first line that is definitely not a header because it goes on and on and really should be considered body text instead of a heading."
    header = extract_section_header(text)
    assert header is None


if __name__ == "__main__":
    test_chunk_text_short()
    test_chunk_text_long()
    test_chunk_text_empty()
    test_compute_file_hash()
    test_compute_file_hash_different()
    test_extract_section_header()
    test_extract_section_header_none()
    print("All ingestion tests passed!")
