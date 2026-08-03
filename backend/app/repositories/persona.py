from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.investor_persona import InvestorPersona
from app.repositories.base import BaseRepository


class PersonaRepository(BaseRepository[InvestorPersona]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, InvestorPersona)

    async def get_by_user(self, user_id: uuid.UUID) -> InvestorPersona | None:
        stmt = select(InvestorPersona).where(InvestorPersona.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def upsert(self, user_id: uuid.UUID, **kwargs) -> InvestorPersona:
        persona = await self.get_by_user(user_id)
        if persona:
            for key, value in kwargs.items():
                setattr(persona, key, value)
        else:
            persona = InvestorPersona(user_id=user_id, **kwargs)
            self.session.add(persona)
        await self.session.flush()
        return persona
