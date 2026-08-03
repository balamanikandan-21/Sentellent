from __future__ import annotations

import math
from datetime import datetime, timezone

from app.memory.types import MemoryEntry


def rank_memories(
    memories: list[MemoryEntry],
    *,
    decay_days: int = 90,
    similarity_weight: float = 0.45,
    confidence_weight: float = 0.30,
    recency_weight: float = 0.25,
) -> list[MemoryEntry]:
    """Rank memories by composite score: similarity + confidence + recency."""
    now = datetime.now(timezone.utc)

    for mem in memories:
        if mem.created_at:
            age_days = (now - mem.created_at.replace(tzinfo=timezone.utc)).days
            mem.recency_score = math.exp(-age_days / decay_days)
        else:
            mem.recency_score = 0.5

        mem.final_rank = (
            similarity_weight * mem.similarity
            + confidence_weight * mem.confidence
            + recency_weight * mem.recency_score
        )

    memories.sort(key=lambda m: m.final_rank, reverse=True)
    return memories
