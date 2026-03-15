from fastapi import APIRouter

from backend.models.chat import ChatRequest, ChatResponse, Citation
from backend.services.embedding_service import generate_embedding
from backend.services.opensearch_service import semantic_search, keyword_search
from backend.services.reranker import hybrid_rerank
from backend.services.llm_service import generate_answer

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_query(request: ChatRequest):
    """Process a user query through the RAG pipeline."""
    query = request.query
    top_k = request.top_k or 5
    alpha = request.alpha or 0.7

    # Step 1: Convert query to embedding
    query_embedding = generate_embedding(query)

    # Step 2: Perform parallel searches (semantic + keyword)
    semantic_results = semantic_search(query_embedding, top_k=top_k * 2)
    keyword_results = keyword_search(query, top_k=top_k * 2)

    # Step 3: Hybrid re-ranking
    ranked_results = hybrid_rerank(
        semantic_results=semantic_results,
        keyword_results=keyword_results,
        alpha=alpha,
        top_k=top_k,
    )

    if not ranked_results:
        return ChatResponse(
            answer="No relevant documents found for your query. Please upload relevant legal documents first.",
            citations=[],
            query=query,
        )

    # Step 4: Generate answer using LLM
    answer = generate_answer(query, ranked_results)

    # Build citations
    citations = [
        Citation(
            source_file=r["source_file"],
            page_number=r["page_number"],
            citation=r["citation"],
            relevance_score=round(r["final_score"], 4),
            text_snippet=r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"],
        )
        for r in ranked_results
    ]

    return ChatResponse(
        answer=answer,
        citations=citations,
        query=query,
    )
