import boto3
import json
from backend.config import settings


def get_bedrock_runtime():
    return boto3.client(
        "bedrock-runtime",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )


def generate_embedding(text: str) -> list[float]:
    """Generate embedding for a single text using Titan Embed v1."""
    client = get_bedrock_runtime()

    response = client.invoke_model(
        modelId=settings.BEDROCK_EMBEDDING_MODEL_ID,
        body=json.dumps({"inputText": text}),
        contentType="application/json",
        accept="application/json",
    )

    result = json.loads(response["body"].read())
    return result["embedding"]


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts.

    Titan Embed v1 doesn't support native batching,
    so we call sequentially but could be parallelized.
    """
    embeddings = []
    for text in texts:
        embedding = generate_embedding(text)
        embeddings.append(embedding)
    return embeddings
