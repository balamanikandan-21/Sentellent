from __future__ import annotations

import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.prompts import RESPONSE_PROMPT
from app.agent.state import AgentState
from app.config.settings import get_settings

logger = structlog.get_logger()


async def generate_response(state: AgentState) -> AgentState:
    query_type = state.get("query_type", "research")

    if query_type == "greeting":
        return {
            **state,
            "response": (
                "Hello! I'm your Sentellent Stock Analyst. I can help you with:\n\n"
                "- **Stock Research** — Ask about any NSE-listed company\n"
                "- **Sentiment Analysis** — Get news sentiment for stocks you follow\n"
                "- **Recommendations** — Get data-driven buy/hold/sell analysis\n\n"
                "Try asking something like *\"What's the latest news on Reliance?\"* "
                "or *\"Should I buy TCS?\"*"
            ),
            "confidence_score": 1.0,
        }

    analysis = state.get("analysis", "")
    citations = state.get("citations", [])
    confidence = state.get("confidence_score", 0.0)

    if not analysis:
        return {
            **state,
            "response": (
                "I don't have sufficient information to answer that question. "
                "Make sure you've followed the relevant tickers so their data is ingested."
            ),
            "confidence_score": 0.0,
        }

    settings = get_settings()
    llm = ChatAnthropic(
        model=settings.PRIMARY_MODEL,
        api_key=settings.ANTHROPIC_API_KEY,
        max_tokens=settings.LLM_MAX_TOKENS,
        temperature=settings.LLM_TEMPERATURE,
    )

    citations_text = "\n".join(
        f"[{i + 1}] {c['source_title']}"
        + (f" ({c.get('source_name', '')})" if c.get("source_name") else "")
        + (f" [{c['published_at'][:10]}]" if c.get("published_at") else "")
        + (f" — {c['source_url']}" if c.get("source_url") else "")
        for i, c in enumerate(citations)
    )

    confidence_note = ""
    if confidence < settings.CONFIDENCE_THRESHOLD:
        confidence_note = (
            "\n\nIMPORTANT: Retrieval confidence is LOW. The response MUST clearly "
            "state that insufficient data is available and avoid speculative claims."
        )
    elif confidence < 0.6:
        confidence_note = (
            "\n\nNOTE: Retrieval confidence is MODERATE. Qualify uncertain claims "
            "with phrases like 'based on limited available data'."
        )

    prompt = RESPONSE_PROMPT.format(
        analysis=analysis,
        citations=citations_text or "No specific sources to cite.",
    ) + confidence_note

    response = await llm.ainvoke([
        SystemMessage(content="You are the Sentellent Stock Analyst assistant."),
        HumanMessage(content=prompt),
    ])

    final_response = (
        response.content if isinstance(response.content, str) else str(response.content)
    )

    if confidence >= settings.CONFIDENCE_THRESHOLD and citations:
        final_response += f"\n\n---\n*Confidence: {confidence:.0%} · {len(citations)} sources*"

    logger.info(
        "response_generated",
        length=len(final_response),
        confidence=round(confidence, 3),
    )
    return {**state, "response": final_response, "confidence_score": confidence}
