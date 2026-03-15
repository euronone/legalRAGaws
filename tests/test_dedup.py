"""Tests for deduplication logic (unit tests only, no AWS calls)."""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.s3_service import compute_file_hash


def test_same_file_same_hash():
    """Identical files should produce identical hashes."""
    content = b"%PDF-1.4 fake pdf content here"
    assert compute_file_hash(content) == compute_file_hash(content)


def test_different_file_different_hash():
    """Different files should produce different hashes."""
    assert compute_file_hash(b"file A") != compute_file_hash(b"file B")


def test_hash_is_sha256():
    """Hash should be 64 hex characters (SHA-256)."""
    h = compute_file_hash(b"test")
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_empty_file_has_hash():
    """Even empty content should produce a valid hash."""
    h = compute_file_hash(b"")
    assert len(h) == 64


if __name__ == "__main__":
    test_same_file_same_hash()
    test_different_file_different_hash()
    test_hash_is_sha256()
    test_empty_file_has_hash()
    print("All dedup tests passed!")
