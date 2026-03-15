from backend.services.s3_service import compute_file_hash
from backend.services.opensearch_service import is_file_processed


def check_duplicate(file_bytes: bytes) -> tuple[bool, str]:
    """Check if a file has already been processed.

    Returns:
        (is_duplicate, file_hash)
    """
    file_hash = compute_file_hash(file_bytes)
    is_dup = is_file_processed(file_hash)
    return is_dup, file_hash
