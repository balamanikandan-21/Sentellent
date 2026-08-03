from __future__ import annotations

import structlog

from app.rag.types import RetrievedChunk

logger = structlog.get_logger()


def compute_confidence(
    chunks: list[RetrievedChunk],
    candidate_count: int,
) -> float:
    """Compute retrieval confidence from 0.0 to 1.0.

    Factors:
    - Average relevance score of reranked chunks (40%)
    - Best single chunk score (25%)
    - Coverage: ratio of high-quality chunks (score > 0.5) (20%)
    - Diversity: unique article sources (15%)
    """
    if not chunks:
        return 0.0

    scores = [c.rerank_score or c.combined_score for c in chunks]
    avg_score = sum(scores) / len(scores)
    best_score = max(scores)
    high_quality = sum(1 for s in scores if s > 0.5) / max(len(scores), 1)
    unique_articles = len({c.article_id for c in chunks})
    diversity = min(unique_articles / max(len(chunks), 1), 1.0)

    confidence = (
        0.40 * avg_score
        + 0.25 * best_score
        + 0.20 * high_quality
        + 0.15 * diversity
    )

    confidence = max(0.0, min(1.0, confidence))

    logger.info(
        "confidence_computed",
        confidence=round(confidence, 3),
        avg_score=round(avg_score, 3),
        best_score=round(best_score, 3),
        high_quality_ratio=round(high_quality, 3),
        diversity=round(diversity, 3),
        chunk_count=len(chunks),
    )
    return confidence
