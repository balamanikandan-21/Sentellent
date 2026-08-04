from __future__ import annotations

import uuid

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.ingestion.processors.embeddings import generate_single_embedding
from app.memory.extractor import ExtractedMemory, extract_memories
from app.memory.ranker import rank_memories
from app.memory.types import MemoryEntry, MemoryProfile
from app.repositories.memory import MemoryRepository
from app.repositories.persona import PersonaRepository

logger = structlog.get_logger()

_CATEGORY_TO_PERSONA_FIELD = {
    "risk_appetite": "risk_tolerance",
    "investment_style": "investment_style",
    "investment_goals": "investment_goals",
}

_CATEGORY_TO_PERSONA_LIST = {
    "preferred_stocks": "preferred_tickers",
    "avoided_stocks": "avoided_tickers",
    "sector_preferences": "sector_preferences",
}


class MemoryStore:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.memory_repo = MemoryRepository(db)
        self.persona_repo = PersonaRepository(db)

    async def retrieve_profile(
        self,
        user_id: uuid.UUID,
        query: str | None = None,
    ) -> MemoryProfile:
        persona = await self.persona_repo.get_by_user(user_id)

        profile = MemoryProfile(
            risk_appetite=persona.risk_tolerance if persona else None,
            investment_style=persona.investment_style if persona else None,
            investment_horizon=persona.investment_horizon if persona else None,
            investment_goals=persona.investment_goals if persona else None,
            preferred_tickers=list(persona.preferred_tickers or []) if persona else [],
            avoided_tickers=list(persona.avoided_tickers or []) if persona else [],
            sector_preferences=list(persona.sector_preferences or []) if persona else [],
            avoided_sectors=list(persona.avoided_sectors or []) if persona else [],
        )

        if query:
            profile.memories = await self._retrieve_relevant_memories(user_id, query)
        else:
            all_memories = await self.memory_repo.get_active_by_user(user_id, limit=10)
            profile.memories = [
                MemoryEntry(
                    id=str(m.id),
                    category=m.category,
                    content=m.content,
                    confidence=m.confidence,
                    source=m.source,
                    created_at=m.created_at,
                )
                for m in all_memories
            ]

        return profile

    async def _retrieve_relevant_memories(
        self,
        user_id: uuid.UUID,
        query: str,
    ) -> list[MemoryEntry]:
        settings = get_settings()

        try:
            query_embedding = await generate_single_embedding(query)
        except Exception:
            logger.exception("memory_embedding_failed")
            return []

        results = await self.memory_repo.search_similar(
            user_id,
            query_embedding,
            limit=settings.MEMORY_TOP_K,
            threshold=settings.MEMORY_SIMILARITY_THRESHOLD,
        )

        entries = [
            MemoryEntry(
                id=str(mem.id),
                category=mem.category,
                content=mem.content,
                confidence=mem.confidence,
                source=mem.source,
                similarity=sim,
                created_at=mem.created_at,
            )
            for mem, sim in results
        ]

        ranked = rank_memories(entries, decay_days=settings.MEMORY_DECAY_DAYS)

        for entry in ranked:
            try:
                await self.memory_repo.touch(uuid.UUID(entry.id))
            except Exception:
                pass

        logger.info(
            "memories_retrieved",
            count=len(ranked),
            top_rank=round(ranked[0].final_rank, 3) if ranked else 0,
        )
        return ranked

    async def process_and_store(
        self,
        user_id: uuid.UUID,
        query: str,
        chat_history: list[dict],
    ) -> list[str]:
        extracted = await extract_memories(query, chat_history)

        if not extracted:
            return []

        stored_summaries: list[str] = []
        persona_updates: dict = {}

        for mem in extracted:
            if mem.supersedes:
                await self._handle_supersede(user_id, mem)

            try:
                embedding = await generate_single_embedding(mem.content)
            except Exception:
                logger.exception("memory_store_embedding_failed", content=mem.content[:50])
                embedding = None

            await self.memory_repo.upsert(
                user_id=user_id,
                category=mem.category,
                content=mem.content,
                embedding=embedding,
                confidence=mem.confidence,
                source="inferred",
            )

            self._collect_persona_update(mem, persona_updates)
            stored_summaries.append(f"[{mem.category}] {mem.content}")

        if persona_updates:
            await self.persona_repo.upsert(user_id, **persona_updates)

            persona = await self.persona_repo.get_by_user(user_id)
            if persona:
                try:
                    profile_text = self._build_profile_text(persona)
                    persona_embedding = await generate_single_embedding(profile_text)
                    await self.persona_repo.upsert(user_id, embedding=persona_embedding)
                except Exception:
                    logger.exception("persona_embedding_update_failed")

        await self.db.commit()

        logger.info(
            "memories_stored",
            count=len(stored_summaries),
            persona_fields=list(persona_updates.keys()),
        )
        return stored_summaries

    async def _handle_supersede(self, user_id: uuid.UUID, mem: ExtractedMemory) -> None:
        existing = await self.memory_repo.get_by_category(user_id, mem.category)
        for old_mem in existing:
            if mem.supersedes and mem.supersedes.lower() in old_mem.content.lower():
                await self.memory_repo.deactivate(old_mem.id)
                logger.info(
                    "memory_superseded",
                    old=old_mem.content[:60],
                    new=mem.content[:60],
                )

    def _collect_persona_update(self, mem: ExtractedMemory, updates: dict) -> None:
        if mem.category in _CATEGORY_TO_PERSONA_FIELD:
            field_name = _CATEGORY_TO_PERSONA_FIELD[mem.category]
            updates[field_name] = mem.content

        elif mem.category in _CATEGORY_TO_PERSONA_LIST:
            field_name = _CATEGORY_TO_PERSONA_LIST[mem.category]
            tickers = [
                t.strip().upper()
                for t in mem.content.replace(",", " ").split()
                if t.strip().isalpha() and len(t.strip()) <= 20
            ]
            if tickers:
                existing = updates.get(field_name, [])
                updates[field_name] = list(set(existing + tickers))

    @staticmethod
    def _build_profile_text(persona) -> str:
        parts = []
        if persona.risk_tolerance:
            parts.append(f"Risk: {persona.risk_tolerance}")
        if persona.investment_style:
            parts.append(f"Style: {persona.investment_style}")
        if persona.investment_horizon:
            parts.append(f"Horizon: {persona.investment_horizon}")
        if persona.investment_goals:
            parts.append(f"Goals: {persona.investment_goals}")
        if persona.preferred_tickers:
            parts.append(f"Preferred: {', '.join(persona.preferred_tickers)}")
        if persona.avoided_tickers:
            parts.append(f"Avoided: {', '.join(persona.avoided_tickers)}")
        if persona.sector_preferences:
            parts.append(f"Sectors: {', '.join(persona.sector_preferences)}")
        return ". ".join(parts) if parts else "New investor, no preferences yet."
