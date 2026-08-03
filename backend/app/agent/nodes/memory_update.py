from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import AgentState
from app.memory.store import MemoryStore

logger = structlog.get_logger()


async def update_memory(state: AgentState, db: AsyncSession) -> AgentState:
    query_type = state.get("query_type", "research")
    if query_type == "greeting":
        return state

    memory_store = MemoryStore(db)
    chat_history = state.get("chat_history", [])

    stored = await memory_store.process_and_store(
        user_id=state["user_id"],
        query=state["query"],
        chat_history=chat_history,
    )

    if stored:
        logger.info("memory_updated", count=len(stored), items=stored)

    return state
