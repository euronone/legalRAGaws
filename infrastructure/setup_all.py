"""
Orchestrator: Provisions all AWS resources for the Legal RAG system.

Usage:
    python infrastructure/setup_all.py

Requires .env file with AWS credentials.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from backend.config import settings


def main():
    print("=" * 60)
    print("  Legal RAG System - AWS Infrastructure Setup")
    print("=" * 60)

    # Validate credentials
    if not settings.AWS_ACCESS_KEY_ID or not settings.AWS_SECRET_ACCESS_KEY:
        print("\n[ERROR] AWS credentials not found in .env file.")
        print("        Copy .env.example to .env and fill in your credentials.")
        sys.exit(1)

    print(f"\nRegion: {settings.AWS_REGION}")
    print(f"S3 Bucket: {settings.S3_BUCKET_NAME}")
    print(f"OpenSearch Domain: {settings.OPENSEARCH_DOMAIN_NAME}")
    print(f"Embedding Model: {settings.BEDROCK_EMBEDDING_MODEL_ID}")
    print(f"LLM Model: {settings.BEDROCK_LLM_MODEL_ID}")
    print()

    # Step 1: S3
    print("-" * 40)
    print("Step 1: S3 Bucket")
    print("-" * 40)
    from infrastructure.setup_s3 import create_s3_bucket
    create_s3_bucket()
    print()

    # Step 2: Bedrock
    print("-" * 40)
    print("Step 2: Bedrock Model Access")
    print("-" * 40)
    from infrastructure.setup_bedrock import verify_bedrock_access
    bedrock_ok = verify_bedrock_access()
    if not bedrock_ok:
        print("\n[WARN] Some Bedrock models need access. Enable them in the AWS console.")
        print("       Continuing with setup...")
    print()

    # Step 3: OpenSearch
    print("-" * 40)
    print("Step 3: OpenSearch Domain")
    print("-" * 40)
    from infrastructure.setup_opensearch import create_opensearch_domain, create_indices
    endpoint = create_opensearch_domain()
    if endpoint:
        # Save endpoint to .env if not already there
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                env_content = f.read()
            if "OPENSEARCH_ENDPOINT=" not in env_content or env_content.split("OPENSEARCH_ENDPOINT=")[1].split("\n")[0].strip() == "":
                with open(env_path, "a") as f:
                    f.write(f"\nOPENSEARCH_ENDPOINT={endpoint}\n")
                print(f"[OK] Saved OpenSearch endpoint to .env")
        # Create indices
        create_indices(endpoint)
    print()

    print("=" * 60)
    print("  Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Run the backend:  uvicorn backend.main:app --reload --port 8000")
    print("  2. Run the frontend: streamlit run frontend/app.py")


if __name__ == "__main__":
    main()
