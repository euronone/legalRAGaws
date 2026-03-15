"""Tests for the query pipeline (re-ranking logic)."""
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.reranker import normalize_scores, hybrid_rerank


def test_normalize_scores():
    """Scores should be normalized to [0, 1]."""
    results = [
        {"score": 0.2, "text": "a"},
        {"score": 0.8, "text": "b"},
        {"score": 0.5, "text": "c"},
    ]
    normalized = normalize_scores(results)
    assert normalized[0]["normalized_score"] == 0.0  # min
    assert normalized[1]["normalized_score"] == 1.0  # max
    assert 0.0 <= normalized[2]["normalized_score"] <= 1.0


def test_normalize_scores_single():
    """Single result should get score of 1.0."""
    results = [{"score": 0.5, "text": "a"}]
    normalized = normalize_scores(results)
    assert normalized[0]["normalized_score"] == 1.0


def test_normalize_scores_empty():
    """Empty list should return empty."""
    assert normalize_scores([]) == []


def _make_result(file_hash, chunk_index, score, search_type):
    return {
        "text": f"chunk {chunk_index}",
        "source_file": "test.pdf",
        "s3_key": "documents/test.pdf",
        "page_number": 1,
        "chunk_index": chunk_index,
        "section_header": None,
        "file_hash": file_hash,
        "citation": f"test.pdf, Page 1",
        "uploaded_at": "2024-01-01",
        "score": score,
        "search_type": search_type,
    }


def test_hybrid_rerank_deduplication():
    """Same chunk in both results should be merged, not duplicated."""
    semantic = [_make_result("abc", 0, 0.9, "semantic")]
    keyword = [_make_result("abc", 0, 0.8, "keyword")]

    ranked = hybrid_rerank(semantic, keyword, alpha=0.7, top_k=5)
    assert len(ranked) == 1
    assert ranked[0]["final_score"] > 0


def test_hybrid_rerank_ordering():
    """Higher scoring results should come first."""
    semantic = [
        _make_result("abc", 0, 0.9, "semantic"),
        _make_result("abc", 1, 0.3, "semantic"),
    ]
    keyword = [
        _make_result("abc", 1, 0.9, "keyword"),
        _make_result("abc", 0, 0.1, "keyword"),
    ]

    ranked = hybrid_rerank(semantic, keyword, alpha=0.5, top_k=5)
    assert len(ranked) == 2
    assert ranked[0]["final_score"] >= ranked[1]["final_score"]


def test_hybrid_rerank_alpha_weighting():
    """Alpha=1.0 should only use semantic scores."""
    semantic = [_make_result("abc", 0, 1.0, "semantic")]
    keyword = [_make_result("abc", 1, 1.0, "keyword")]

    ranked = hybrid_rerank(semantic, keyword, alpha=1.0, top_k=5)
    # The semantic-only result should rank highest
    assert ranked[0]["chunk_index"] == 0


if __name__ == "__main__":
    test_normalize_scores()
    test_normalize_scores_single()
    test_normalize_scores_empty()
    test_hybrid_rerank_deduplication()
    test_hybrid_rerank_ordering()
    test_hybrid_rerank_alpha_weighting()
    print("All query tests passed!")
