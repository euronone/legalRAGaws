import boto3
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.config import settings


def verify_bedrock_access():
    """Verify that the required Bedrock models are accessible."""
    bedrock = boto3.client(
        "bedrock",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    required_models = [
        settings.BEDROCK_EMBEDDING_MODEL_ID,
        settings.BEDROCK_LLM_MODEL_ID,
    ]

    print("[..] Checking Bedrock model access...")

    # List available foundation models
    response = bedrock.list_foundation_models()
    available_model_ids = {m["modelId"] for m in response["modelSummaries"]}

    all_ok = True
    for model_id in required_models:
        if model_id in available_model_ids:
            print(f"[OK] Model '{model_id}' is available.")
        else:
            print(f"[!!] Model '{model_id}' not found in available models.")
            print(f"     You may need to request access in the AWS Bedrock console.")
            all_ok = False

    # Test embedding model with a quick invocation
    try:
        bedrock_runtime = boto3.client(
            "bedrock-runtime",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )

        import json
        response = bedrock_runtime.invoke_model(
            modelId=settings.BEDROCK_EMBEDDING_MODEL_ID,
            body=json.dumps({"inputText": "test"}),
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        dim = len(result.get("embedding", []))
        print(f"[OK] Embedding model test passed. Output dimension: {dim}")
    except Exception as e:
        print(f"[!!] Embedding model test failed: {e}")
        all_ok = False

    # Test LLM model (Nova format)
    try:
        response = bedrock_runtime.invoke_model(
            modelId=settings.BEDROCK_LLM_MODEL_ID,
            body=json.dumps({
                "messages": [
                    {"role": "user", "content": [{"text": "Say hello."}]}
                ],
                "inferenceConfig": {
                    "max_new_tokens": 10,
                    "temperature": 0.1,
                }
            }),
            contentType="application/json",
            accept="application/json",
        )
        result = json.loads(response["body"].read())
        print(f"[OK] LLM model test passed.")
    except Exception as e:
        print(f"[!!] LLM model test failed: {e}")
        all_ok = False

    return all_ok


if __name__ == "__main__":
    verify_bedrock_access()
