import boto3
import hashlib
from datetime import datetime, timezone
from backend.config import settings


def get_s3_client():
    return boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


def compute_file_hash(file_bytes: bytes) -> str:
    """Compute SHA-256 hash of file content."""
    return hashlib.sha256(file_bytes).hexdigest()


def upload_file_to_s3(file_bytes: bytes, filename: str) -> str:
    """Upload file to S3 and return the S3 key."""
    s3 = get_s3_client()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    s3_key = f"documents/{timestamp}_{filename}"
    file_hash = compute_file_hash(file_bytes)

    s3.put_object(
        Bucket=settings.S3_BUCKET_NAME,
        Key=s3_key,
        Body=file_bytes,
        Metadata={
            "original_filename": filename,
            "upload_time": timestamp,
            "content_hash": file_hash,
        },
    )

    return s3_key


def download_file_from_s3(s3_key: str) -> bytes:
    """Download file from S3."""
    s3 = get_s3_client()
    response = s3.get_object(Bucket=settings.S3_BUCKET_NAME, Key=s3_key)
    return response["Body"].read()


def list_files_in_s3(prefix: str = "documents/") -> list[dict]:
    """List files in the S3 bucket under the given prefix."""
    s3 = get_s3_client()
    response = s3.list_objects_v2(Bucket=settings.S3_BUCKET_NAME, Prefix=prefix)
    files = []
    for obj in response.get("Contents", []):
        if obj["Key"] != prefix:  # skip the folder marker
            files.append({
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
            })
    return files
