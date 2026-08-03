from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.repositories.base import BaseRepository


class ChatRepository(BaseRepository[ChatSession]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ChatSession)

    async def create_session(self, user_id: uuid.UUID, title: str = "New Chat") -> ChatSession:
        chat_session = ChatSession(user_id=user_id, title=title)
        self.session.add(chat_session)
        await self.session.flush()
        return chat_session

    async def list_sessions(
        self, user_id: uuid.UUID, *, offset: int = 0, limit: int = 50
    ) -> Sequence[ChatSession]:
        stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_session(self, session_id: uuid.UUID, user_id: uuid.UUID) -> ChatSession | None:
        stmt = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_message(
        self,
        session_id: uuid.UUID,
        role: str,
        content: str,
        *,
        citations: dict | None = None,
        token_count: int | None = None,
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            citations=citations,
            token_count=token_count,
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def get_messages(
        self, session_id: uuid.UUID, *, limit: int = 100
    ) -> Sequence[ChatMessage]:
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_session(self, chat_session: ChatSession) -> None:
        await self.session.delete(chat_session)
        await self.session.flush()
