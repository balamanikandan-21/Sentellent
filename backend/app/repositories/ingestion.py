from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ingestion_job import IngestionJob
from app.repositories.base import BaseRepository


class IngestionRepository(BaseRepository[IngestionJob]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, IngestionJob)

    async def get_by_idempotency_key(self, key: str) -> IngestionJob | None:
        stmt = select(IngestionJob).where(IngestionJob.idempotency_key == key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_running(self, job: IngestionJob) -> IngestionJob:
        job.status = "running"
        job.started_at = datetime.utcnow()
        await self.session.flush()
        return job

    async def mark_completed(self, job: IngestionJob, articles_processed: int) -> IngestionJob:
        job.status = "completed"
        job.articles_processed = articles_processed
        job.completed_at = datetime.utcnow()
        await self.session.flush()
        return job

    async def mark_failed(self, job: IngestionJob, error: str) -> IngestionJob:
        job.status = "failed"
        job.error_message = error
        job.completed_at = datetime.utcnow()
        await self.session.flush()
        return job
