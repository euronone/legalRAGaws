from backend.config import settings


def normalize_scores(results: list[dict]) -> list[dict]:
    """Normalize scores to [0, 1] range using min-max normalization."""
    if not results:
        return results

    scores = [r["score"] for r in results]
    min_score = min(scores)
    max_score = max(scores)
    score_range = max_score - min_score

    for r in results:
        if score_range > 0:
            r["normalized_score"] = (r["score"] - min_score) / score_range
        else:
            r["normalized_score"] = 1.0

    return results


def hybrid_rerank(
    semantic_results: list[dict],
    keyword_results: list[dict],
    alpha: float = None,
    top_k: int = None,
) -> list[dict]:
    """Re-rank results using hybrid scoring.

    final_score = alpha * semantic_score + (1 - alpha) * keyword_score

    Args:
        semantic_results: Results from k-NN vector search
        keyword_results: Results from BM25 keyword search
        alpha: Weight for semantic similarity (default from config)
        top_k: Number of results to return (default from config)

    Returns:
        Re-ranked and deduplicated results
    """
    alpha = alpha if alpha is not None else settings.RERANK_ALPHA
    top_k = top_k or settings.TOP_K

    # Normalize scores within each result set
    semantic_results = normalize_scores(semantic_results)
    keyword_results = normalize_scores(keyword_results)

    # Build a merged map keyed by chunk identity (file_hash + chunk_index)
    merged = {}

    for r in semantic_results:
        key = f"{r['file_hash']}_{r['chunk_index']}"
        merged[key] = {
            "text": r["text"],
            "source_file": r["source_file"],
            "s3_key": r["s3_key"],
            "page_number": r["page_number"],
            "chunk_index": r["chunk_index"],
            "section_header": r.get("section_header"),
            "file_hash": r["file_hash"],
            "citation": r["citation"],
            "uploaded_at": r.get("uploaded_at"),
            "semantic_score": r["normalized_score"],
            "keyword_score": 0.0,
        }

    for r in keyword_results:
        key = f"{r['file_hash']}_{r['chunk_index']}"
        if key in merged:
            merged[key]["keyword_score"] = r["normalized_score"]
        else:
            merged[key] = {
                "text": r["text"],
                "source_file": r["source_file"],
                "s3_key": r["s3_key"],
                "page_number": r["page_number"],
                "chunk_index": r["chunk_index"],
                "section_header": r.get("section_header"),
                "file_hash": r["file_hash"],
                "citation": r["citation"],
                "uploaded_at": r.get("uploaded_at"),
                "semantic_score": 0.0,
                "keyword_score": r["normalized_score"],
            }

    # Compute final hybrid score
    for key in merged:
        entry = merged[key]
        entry["final_score"] = (
            alpha * entry["semantic_score"]
            + (1 - alpha) * entry["keyword_score"]
        )

    # Sort by final score descending and return top_k
    ranked = sorted(merged.values(), key=lambda x: x["final_score"], reverse=True)
    return ranked[:top_k]
