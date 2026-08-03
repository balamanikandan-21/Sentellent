from __future__ import annotations

import json

import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.agent.prompts import ROUTER_PROMPT
from app.agent.state import AgentState
from app.config.settings import get_settings

logger = structlog.get_logger()


async def route_query(state: AgentState) -> AgentState:
    settings = get_settings()
    llm = ChatAnthropic(
        model=settings.TAGGING_MODEL,
        api_key=settings.ANTHROPIC_API_KEY,
        max_tokens=256,
        temperature=0,
    )

    response = await llm.ainvoke([
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=state["query"]),
    ])

    try:
        result = json.loads(response.content)
        query_type = result.get("query_type", "research")
        tickers = [t.upper() for t in result.get("tickers", [])]
    except (json.JSONDecodeError, AttributeError):
        logger.warning("router_parse_failed", raw=response.content)
        query_type = "research"
        tickers = []

    logger.info("query_routed", query_type=query_type, tickers=tickers)
    return {**state, "query_type": query_type, "tickers_mentioned": tickers}
