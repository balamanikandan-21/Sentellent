from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

MEMORY_CATEGORIES = (
    "risk_appetite",
    "investment_style",
    "sector_preferences",
    "investment_goals",
    "avoided_stocks",
    "preferred_stocks",
    "general",
)


@dataclass
class MemoryEntry:
    id: str
    category: str
    content: str
    confidence: float
    source: str
    similarity: float = 0.0
    recency_score: float = 0.0
    final_rank: float = 0.0
    created_at: datetime | None = None


@dataclass
class MemoryProfile:
    risk_appetite: str | None = None
    investment_style: str | None = None
    investment_horizon: str | None = None
    investment_goals: str | None = None
    preferred_tickers: list[str] = field(default_factory=list)
    avoided_tickers: list[str] = field(default_factory=list)
    sector_preferences: list[str] = field(default_factory=list)
    avoided_sectors: list[str] = field(default_factory=list)
    memories: list[MemoryEntry] = field(default_factory=list)

    def to_prompt_text(self) -> str:
        parts = []
        if self.risk_appetite:
            parts.append(f"Risk appetite: {self.risk_appetite}")
        if self.investment_style:
            parts.append(f"Investment style: {self.investment_style}")
        if self.investment_horizon:
            parts.append(f"Investment horizon: {self.investment_horizon}")
        if self.investment_goals:
            parts.append(f"Goals: {self.investment_goals}")
        if self.preferred_tickers:
            parts.append(f"Preferred stocks: {', '.join(self.preferred_tickers)}")
        if self.avoided_tickers:
            parts.append(f"Avoided stocks: {', '.join(self.avoided_tickers)}")
        if self.sector_preferences:
            parts.append(f"Preferred sectors: {', '.join(self.sector_preferences)}")
        if self.avoided_sectors:
            parts.append(f"Avoided sectors: {', '.join(self.avoided_sectors)}")
        if self.memories:
            parts.append("\nRelevant past preferences:")
            for m in self.memories[:5]:
                parts.append(f"  - [{m.category}] {m.content} (confidence: {m.confidence:.0%})")
        if not parts:
            return "No investor profile available."
        return "\n".join(parts)
