from datetime import datetime, timezone

from app.rag.confidence import compute_confidence
from app.rag.types import RetrievedChunk


def _chunk(article_id: str, combined: float, rerank: float | None = None) -> RetrievedChunk:
    return RetrievedChunk(
        content="text",
        article_id=article_id,
        chunk_index=0,
        article_title="t",
        article_url="https://example.com",
        article_source="MoneyControl",
        published_at=datetime.now(timezone.utc),
        sentiment=None,
        category=None,
        vector_score=combined,
        keyword_score=combined,
        combined_score=combined,
        rerank_score=rerank,
    )


class TestComputeConfidence:
    def test_empty_chunks_zero_confidence(self):
        assert compute_confidence([], candidate_count=0) == 0.0

    def test_high_relevance_diverse_sources(self):
        chunks = [_chunk(f"a{i}", 0.9, rerank=0.9) for i in range(4)]
        c = compute_confidence(chunks, candidate_count=10)
        assert c > 0.8

    def test_low_relevance_yields_low_confidence(self):
        chunks = [_chunk(f"a{i}", 0.1, rerank=0.1) for i in range(4)]
        c = compute_confidence(chunks, candidate_count=10)
        assert c < 0.35  # below anti-hallucination threshold

    def test_rerank_score_preferred_over_combined(self):
        # combined says relevant, reranker says not — reranker wins
        chunks = [_chunk("a", 0.95, rerank=0.05)]
        c_reranked = compute_confidence(chunks, candidate_count=5)
        c_unranked = compute_confidence([_chunk("a", 0.95)], candidate_count=5)
        assert c_reranked < c_unranked

    def test_duplicate_sources_reduce_confidence(self):
        same_article = [_chunk("same", 0.8, rerank=0.8) for _ in range(4)]
        distinct = [_chunk(f"a{i}", 0.8, rerank=0.8) for i in range(4)]
        assert compute_confidence(same_article, 8) < compute_confidence(distinct, 8)

    def test_bounded_zero_one(self):
        chunks = [_chunk("a", 1.0, rerank=1.0)]
        assert 0.0 <= compute_confidence(chunks, 1) <= 1.0
