import boto3
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config import settings


def create_s3_bucket():
    """Create S3 bucket with versioning and encryption."""
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    bucket_name = settings.S3_BUCKET_NAME

    # Check if bucket already exists
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"[OK] S3 bucket '{bucket_name}' already exists.")
        return bucket_name
    except s3.exceptions.ClientError:
        pass

    # Create bucket
    print(f"[..] Creating S3 bucket '{bucket_name}'...")
    create_params = {"Bucket": bucket_name}
    if settings.AWS_REGION != "us-east-1":
        create_params["CreateBucketConfiguration"] = {
            "LocationConstraint": settings.AWS_REGION
        }
    s3.create_bucket(**create_params)

    # Enable versioning
    s3.put_bucket_versioning(
        Bucket=bucket_name,
        VersioningConfiguration={"Status": "Enabled"},
    )

    # Enable server-side encryption
    s3.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        },
    )

    # Block public access
    s3.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True,
        },
    )

    # Create folder structure
    for prefix in ["documents/", "processed/"]:
        s3.put_object(Bucket=bucket_name, Key=prefix, Body="")

    print(f"[OK] S3 bucket '{bucket_name}' created with versioning + encryption.")
    return bucket_name


if __name__ == "__main__":
    create_s3_bucket()
