from __future__ import annotations

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import AgentState
from app.config.settings import get_settings
from app.memory.store import MemoryStore
from app.repositories.chat import ChatRepository

logger = structlog.get_logger()


async def retrieve_memory(state: AgentState, db: AsyncSession) -> AgentState:
    settings = get_settings()
    chat_repo = ChatRepository(db)

    messages = await chat_repo.get_messages(state["session_id"], limit=settings.CHAT_HISTORY_LIMIT)

    history = [{"role": msg.role, "content": msg.content} for msg in messages]

    memory_store = MemoryStore(db)
    profile = await memory_store.retrieve_profile(state["user_id"], query=state.get("query"))

    logger.info(
        "memory_retrieved",
        message_count=len(history),
        memory_count=len(profile.memories),
    )
    return {**state, "chat_history": history, "memory_profile": profile}
