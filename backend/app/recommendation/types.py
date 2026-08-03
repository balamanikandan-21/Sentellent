from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FactorScore:
    name: str
    score: float
    weight: float
    data_available: bool
    reasoning: str
    sources: list[str] = field(default_factory=list)

    @property
    def weighted(self) -> float:
        return self.score * self.weight if self.data_available else 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "score": round(self.score, 2),
            "weight": self.weight,
            "weighted_score": round(self.weighted, 2),
            "data_available": self.data_available,
            "reasoning": self.reasoning,
            "sources": self.sources,
        }


@dataclass
class ScoreCard:
    ticker: str
    factors: list[FactorScore] = field(default_factory=list)

    @property
    def composite_score(self) -> float:
        total_weight = sum(f.weight for f in self.factors if f.data_available)
        if total_weight == 0:
            return 0.0
        return sum(f.weighted for f in self.factors) / total_weight

    @property
    def data_coverage(self) -> float:
        if not self.factors:
            return 0.0
        return sum(1 for f in self.factors if f.data_available) / len(self.factors)

    @property
    def action(self) -> str:
        s = self.composite_score
        if s >= 0.65:
            return "BUY"
        if s <= 0.35:
            return "SELL"
        return "HOLD"

    @property
    def confidence(self) -> str:
        coverage = self.data_coverage
        if coverage >= 0.75:
            return "high"
        if coverage >= 0.5:
            return "medium"
        return "low"

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "composite_score": round(self.composite_score, 3),
            "action": self.action,
            "confidence": self.confidence,
            "data_coverage": round(self.data_coverage, 2),
            "factors": [f.to_dict() for f in self.factors],
        }


@dataclass
class RecommendationResult:
    ticker: str
    action: str
    composite_score: float
    confidence: float
    scorecard: ScoreCard
    reasoning: str
    citations: list[dict] = field(default_factory=list)
    retrieval_confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "ticker": self.ticker,
            "action": self.action,
            "confidence": self.confidence,
            "composite_score": round(self.composite_score, 3),
            "reasoning": self.reasoning,
            "retrieval_confidence": round(self.retrieval_confidence, 3),
            "scorecard": self.scorecard.to_dict(),
        }
