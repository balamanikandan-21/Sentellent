from __future__ import annotations

import uuid
from datetime import datetime
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_memory import UserMemory


class MemoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_active_by_user(
        self, user_id: uuid.UUID, *, limit: int = 50
    ) -> Sequence[UserMemory]:
        stmt = (
            select(UserMemory)
            .where(UserMemory.user_id == user_id, UserMemory.active == True)  # noqa: E712
            .order_by(UserMemory.updated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_category(
        self, user_id: uuid.UUID, category: str, *, limit: int = 20
    ) -> Sequence[UserMemory]:
        stmt = (
            select(UserMemory)
            .where(
                UserMemory.user_id == user_id,
                UserMemory.category == category,
                UserMemory.active == True,  # noqa: E712
            )
            .order_by(UserMemory.confidence.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search_similar(
        self,
        user_id: uuid.UUID,
        embedding: list[float],
        *,
        limit: int = 10,
        threshold: float = 0.3,
    ) -> list[tuple[UserMemory, float]]:
        stmt = (
            select(
                UserMemory,
                (1 - UserMemory.embedding.cosine_distance(embedding)).label("similarity"),
            )
            .where(
                UserMemory.user_id == user_id,
                UserMemory.active == True,  # noqa: E712
            )
            .order_by(UserMemory.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        return [(mem, float(sim)) for mem, sim in rows if sim >= threshold]

    async def find_duplicate(
        self, user_id: uuid.UUID, category: str, content: str
    ) -> UserMemory | None:
        stmt = (
            select(UserMemory)
            .where(
                UserMemory.user_id == user_id,
                UserMemory.category == category,
                UserMemory.active == True,  # noqa: E712
            )
        )
        result = await self.session.execute(stmt)
        existing = result.scalars().all()

        content_lower = content.lower().strip()
        for mem in existing:
            if mem.content.lower().strip() == content_lower:
                return mem

        return None

    async def upsert(
        self,
        user_id: uuid.UUID,
        category: str,
        content: str,
        embedding: list[float] | None = None,
        confidence: float = 0.8,
        source: str = "inferred",
    ) -> UserMemory:
        existing = await self.find_duplicate(user_id, category, content)
        if existing:
            existing.confidence = max(existing.confidence, confidence)
            existing.source = source
            if embedding:
                existing.embedding = embedding
            await self.session.flush()
            return existing

        memory = UserMemory(
            user_id=user_id,
            category=category,
            content=content,
            embedding=embedding,
            confidence=confidence,
            source=source,
        )
        self.session.add(memory)
        await self.session.flush()
        return memory

    async def deactivate(self, memory_id: uuid.UUID) -> None:
        stmt = (
            update(UserMemory)
            .where(UserMemory.id == memory_id)
            .values(active=False)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def deactivate_by_category(
        self, user_id: uuid.UUID, category: str
    ) -> int:
        stmt = (
            update(UserMemory)
            .where(
                UserMemory.user_id == user_id,
                UserMemory.category == category,
                UserMemory.active == True,  # noqa: E712
            )
            .values(active=False)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount

    async def touch(self, memory_id: uuid.UUID) -> None:
        stmt = (
            update(UserMemory)
            .where(UserMemory.id == memory_id)
            .values(accessed_at=datetime.utcnow())
        )
        await self.session.execute(stmt)
