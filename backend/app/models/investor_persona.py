from __future__ import annotations

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class InvestorPersona(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "investor_personas"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    risk_tolerance: Mapped[str | None] = mapped_column(String(20))
    investment_horizon: Mapped[str | None] = mapped_column(String(20))
    investment_style: Mapped[str | None] = mapped_column(String(30))
    investment_goals: Mapped[str | None] = mapped_column(Text)
    preferred_tickers: Mapped[list[str] | None] = mapped_column(ARRAY(String(20)))
    avoided_tickers: Mapped[list[str] | None] = mapped_column(ARRAY(String(20)))
    sector_preferences: Mapped[list[str] | None] = mapped_column(ARRAY(String(50)))
    avoided_sectors: Mapped[list[str] | None] = mapped_column(ARRAY(String(50)))
    preferences: Mapped[dict | None] = mapped_column(JSONB)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
