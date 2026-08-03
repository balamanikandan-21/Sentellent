from app.recommendation.types import FactorScore, RecommendationResult, ScoreCard

__all__ = ["RecommendationEngine", "FactorScore", "RecommendationResult", "ScoreCard"]


def __getattr__(name: str):
    # Lazy import: the engine pulls in the Anthropic client, which the pure
    # scoring types/tests don't need.
    if name == "RecommendationEngine":
        from app.recommendation.engine import RecommendationEngine

        return RecommendationEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
