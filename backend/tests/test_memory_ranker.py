from datetime import UTC, datetime, timedelta

from app.memory.ranker import rank_memories
from app.memory.types import MemoryEntry


def _memory(
    mem_id: str,
    similarity: float,
    confidence: float,
    age_days: int = 0,
) -> MemoryEntry:
    return MemoryEntry(
        id=mem_id,
        category="general",
        content="test",
        confidence=confidence,
        source="inferred",
        similarity=similarity,
        created_at=datetime.now(UTC) - timedelta(days=age_days),
    )


class TestRankMemories:
    def test_empty_list(self):
        assert rank_memories([]) == []

    def test_higher_similarity_ranks_first(self):
        low = _memory("low", similarity=0.2, confidence=0.8)
        high = _memory("high", similarity=0.9, confidence=0.8)
        ranked = rank_memories([low, high])
        assert ranked[0].id == "high"

    def test_recency_decay_demotes_old_memories(self):
        fresh = _memory("fresh", similarity=0.5, confidence=0.5, age_days=0)
        stale = _memory("stale", similarity=0.5, confidence=0.5, age_days=365)
        ranked = rank_memories([fresh, stale], decay_days=90)
        assert ranked[0].id == "fresh"
        assert stale.recency_score < 0.05  # e^(-365/90)

    def test_confidence_breaks_ties(self):
        sure = _memory("sure", similarity=0.5, confidence=0.95)
        unsure = _memory("unsure", similarity=0.5, confidence=0.2)
        ranked = rank_memories([sure, unsure])
        assert ranked[0].id == "sure"

    def test_final_rank_is_weighted_composite(self):
        m = _memory("m", similarity=1.0, confidence=1.0, age_days=0)
        rank_memories([m], similarity_weight=0.45, confidence_weight=0.30, recency_weight=0.25)
        # fresh memory: recency ~= 1.0, so rank ~= 0.45 + 0.30 + 0.25
        assert abs(m.final_rank - 1.0) < 0.01

    def test_missing_created_at_gets_neutral_recency(self):
        m = MemoryEntry(
            id="x",
            category="general",
            content="t",
            confidence=0.5,
            source="inferred",
            similarity=0.5,
            created_at=None,
        )
        rank_memories([m])
        assert m.recency_score == 0.5
