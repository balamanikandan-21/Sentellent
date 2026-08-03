from __future__ import annotations

import json

import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.prompts import ANALYSIS_PROMPT, SENTIMENT_PROMPT
from app.agent.state import AgentState
from app.config.settings import get_settings

logger = structlog.get_logger()

INSUFFICIENT_DATA = (
    "I don't have sufficient information in my current data to answer this question. "
    "This could mean the relevant stock hasn't been followed yet, or no recent "
    "articles match your query. Try following the ticker first and waiting for "
    "ingestion to complete."
)


def _format_context(chunks: list[dict]) -> str:
    if not chunks:
        return "No relevant documents found in the corpus."
    parts = []
    for i, chunk in enumerate(chunks, 1):
        header = f"[Source {i}]"
        if chunk.get("article_title"):
            header += f" {chunk['article_title']}"
        if chunk.get("article_source"):
            header += f" ({chunk['article_source']})"
        if chunk.get("published_at"):
            header += f" [{chunk['published_at'][:10]}]"

        score = chunk.get("rerank_score") or chunk.get("combined_score", 0)
        header += f" [relevance: {score:.2f}]"

        parts.append(f"{header}\n{chunk['content']}")
    return "\n\n---\n\n".join(parts)


def _format_fundamentals(fundamentals: list[dict]) -> str:
    if not fundamentals:
        return "No fundamentals data available."
    parts = []
    for f in fundamentals:
        parts.append(f"{f['symbol']} ({f['company_name']}) — Sector: {f.get('sector', 'N/A')}")
        if f.get("fundamentals"):
            parts.append(json.dumps(f["fundamentals"], indent=2, default=str))
    return "\n".join(parts)


def _format_persona(persona: dict | None) -> str:
    if not persona:
        return "No investor profile available."
    if persona.get("profile_text"):
        return persona["profile_text"]
    return (
        f"Risk tolerance: {persona.get('risk_tolerance', 'moderate')}, "
        f"Horizon: {persona.get('investment_horizon', 'medium-term')}"
    )


def _format_history(history: list[dict]) -> str:
    if not history:
        return "No prior conversation."
    recent = history[-6:]
    return "\n".join(f"{m['role']}: {m['content'][:200]}" for m in recent)


async def stock_analysis(state: AgentState) -> AgentState:
    confidence = state.get("retrieval_confidence", 0.0)
    settings = get_settings()

    chunks = state.get("retrieved_chunks", [])
    fundamentals = state.get("ticker_fundamentals", [])

    if confidence < settings.CONFIDENCE_THRESHOLD and not fundamentals:
        logger.info(
            "insufficient_context",
            confidence=confidence,
            threshold=settings.CONFIDENCE_THRESHOLD,
        )
        return {
            **state,
            "analysis": INSUFFICIENT_DATA,
            "confidence_score": confidence,
        }

    # NOTE: `temperature` is rejected by Claude Sonnet 5 (400
    # invalid_request_error). Only the Haiku tagging calls still pass it.
    llm = ChatAnthropic(
        model=settings.PRIMARY_MODEL,
        api_key=settings.ANTHROPIC_API_KEY,
        max_tokens=settings.LLM_MAX_TOKENS,
    )

    query_type = state.get("query_type", "research")
    persona = state.get("persona")
    history = state.get("chat_history", [])

    if query_type == "sentiment":
        prompt = SENTIMENT_PROMPT.format(
            context=_format_context(chunks),
            tickers=", ".join(state.get("tickers_mentioned", ["Unknown"])),
            query=state["query"],
        )
    else:
        prompt = ANALYSIS_PROMPT.format(
            context=_format_context(chunks),
            fundamentals=_format_fundamentals(fundamentals),
            persona=_format_persona(persona),
            history=_format_history(history),
            query=state["query"],
            confidence=f"{confidence:.0%}",
        )

    response = await llm.ainvoke([
        SystemMessage(content="You are an expert Indian equity research analyst."),
        HumanMessage(content=prompt),
    ])

    analysis = response.content if isinstance(response.content, str) else str(response.content)
    logger.info(
        "analysis_complete",
        query_type=query_type,
        length=len(analysis),
        confidence=round(confidence, 3),
    )
    return {**state, "analysis": analysis, "confidence_score": confidence}
