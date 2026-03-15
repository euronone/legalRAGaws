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


def build_prompt(query: str, context_chunks: list[dict]) -> str:
    """Build the prompt for the LLM with context and citations."""
    context_parts = []
    for i, chunk in enumerate(context_chunks, 1):
        citation = chunk.get("citation", f"Source {i}")
        text = chunk["text"]
        context_parts.append(f"[{i}] ({citation}):\n{text}")

    context_str = "\n\n".join(context_parts)

    prompt = f"""You are a legal assistant specialized in analyzing legal documents. Answer the user's question based ONLY on the provided context. If the answer cannot be found in the context, clearly state that.

Always include citations in your answer using the format [1], [2], etc., referring to the source numbers provided below.

Context:
{context_str}

Question: {query}

Answer (include citations):"""

    return prompt


def generate_answer(query: str, context_chunks: list[dict]) -> str:
    """Generate an answer using Amazon Nova Lite."""
    client = get_bedrock_runtime()
    prompt = build_prompt(query, context_chunks)

    response = client.invoke_model(
        modelId=settings.BEDROCK_LLM_MODEL_ID,
        body=json.dumps({
            "messages": [
                {"role": "user", "content": [{"text": prompt}]}
            ],
            "inferenceConfig": {
                "max_new_tokens": 2048,
                "temperature": 0.1,
                "top_p": 0.9,
            }
        }),
        contentType="application/json",
        accept="application/json",
    )

    result = json.loads(response["body"].read())
    # Nova response format
    output_text = result.get("output", {}).get("message", {}).get("content", [{}])[0].get("text", "")
    return output_text.strip()
