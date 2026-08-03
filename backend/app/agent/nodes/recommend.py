from __future__ import annotations

import structlog

from app.agent.nodes.analysis import (
    INSUFFICIENT_DATA,
    _format_context,
    _format_fundamentals,
    _format_persona,
)
from app.agent.state import AgentState
from app.config.settings import get_settings
from app.recommendation.engine import RecommendationEngine

logger = structlog.get_logger()


async def generate_recommendation(state: AgentState) -> AgentState:
    settings = get_settings()
    tickers = state.get("tickers_mentioned", [])

    if not tickers:
        return {
            **state,
            "recommendation": None,
            "analysis": state.get("analysis", "")
            + "\n\nNo specific ticker mentioned for recommendation.",
            "confidence_score": state.get("retrieval_confidence", 0.0),
        }

    confidence = state.get("retrieval_confidence", 0.0)
    fundamentals_list = state.get("ticker_fundamentals", [])
    chunks = state.get("retrieved_chunks", [])
    persona = state.get("persona")

    if confidence < settings.CONFIDENCE_THRESHOLD and not fundamentals_list:
        logger.info(
            "insufficient_context_for_recommendation",
            confidence=confidence,
            ticker=tickers[0],
        )
        return {
            **state,
            "recommendation": None,
            "analysis": INSUFFICIENT_DATA,
            "confidence_score": confidence,
        }

    ticker = tickers[0]

    fundamentals_data = None
    for f in fundamentals_list:
        if f["symbol"].upper() == ticker.upper():
            fundamentals_data = f.get("fundamentals") or f
            break
    if not fundamentals_data and fundamentals_list:
        fundamentals_data = fundamentals_list[0].get("fundamentals") or fundamentals_list[0]

    engine = RecommendationEngine()
    scorecard = engine.compute_scorecard(
        ticker=ticker,
        fundamentals_data=fundamentals_data,
        chunks=chunks,
        retrieval_confidence=confidence,
        persona=persona,
    )

    result = await engine.generate(
        ticker=ticker,
        scorecard=scorecard,
        context=_format_context(chunks),
        fundamentals_text=_format_fundamentals(fundamentals_list),
        persona_text=_format_persona(persona),
        query=state["query"],
        retrieval_confidence=confidence,
    )

    recommendation = {
        "ticker": result.ticker,
        "action": result.action,
        "confidence": result.confidence,
        "reasoning": result.reasoning,
        "retrieval_confidence": result.retrieval_confidence,
        "composite_score": result.composite_score,
        "scorecard": result.scorecard.to_dict(),
    }

    analysis = _build_analysis_text(result)

    logger.info(
        "recommendation_complete",
        ticker=ticker,
        action=result.action,
        confidence=round(result.confidence, 3),
        composite=round(result.composite_score, 3),
        factors_available=sum(1 for f in scorecard.factors if f.data_available),
    )
    return {
        **state,
        "analysis": analysis,
        "recommendation": recommendation,
        "confidence_score": confidence,
    }


def _build_analysis_text(result) -> str:
    lines = [result.reasoning, ""]

    card = result.scorecard
    lines.append("**Multi-Factor Scorecard**")
    lines.append(f"| Factor | Score | Status |")
    lines.append(f"|--------|-------|--------|")

    for f in card.factors:
        status = f"{'%.0f' % (f.score * 100)}%" if f.data_available else "N/A"
        avail = "Available" if f.data_available else "Unavailable"
        lines.append(f"| {f.name.replace('_', ' ').title()} | {status} | {avail} |")

    lines.append(f"\n**Composite: {card.composite_score:.0%}** "
                 f"(Data coverage: {card.data_coverage:.0%})")

    lines.append("")
    for f in card.factors:
        if f.data_available and f.reasoning:
            lines.append(f"- **{f.name.replace('_', ' ').title()}**: {f.reasoning}")

    return "\n".join(lines)
