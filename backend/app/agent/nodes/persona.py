from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import AgentState

logger = structlog.get_logger()


async def retrieve_persona(state: AgentState, db: AsyncSession) -> AgentState:
    profile = state.get("memory_profile")
    if not profile:
        logger.info("persona_retrieved", has_persona=False)
        return {**state, "persona": None}

    persona_data = {
        "risk_tolerance": profile.risk_appetite or "moderate",
        "investment_horizon": profile.investment_horizon or "medium-term",
        "investment_style": profile.investment_style,
        "investment_goals": profile.investment_goals,
        "preferred_tickers": profile.preferred_tickers,
        "avoided_tickers": profile.avoided_tickers,
        "sector_preferences": profile.sector_preferences,
        "avoided_sectors": profile.avoided_sectors,
        "profile_text": profile.to_prompt_text(),
    }

    logger.info("persona_retrieved", has_persona=True)
    return {**state, "persona": persona_data}
