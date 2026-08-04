from collections.abc import AsyncGenerator

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import get_redis as _get_redis
from app.db.session import get_session_factory
from app.repositories.article import ArticleRepository
from app.repositories.chat import ChatRepository
from app.repositories.ingestion import IngestionRepository
from app.repositories.memory import MemoryRepository
from app.repositories.persona import PersonaRepository
from app.repositories.recommendation import RecommendationRepository
from app.repositories.ticker import TickerRepository
from app.repositories.user import UserRepository


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def get_redis() -> Redis:
    return await _get_redis()


async def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


async def get_ticker_repo(db: AsyncSession = Depends(get_db)) -> TickerRepository:
    return TickerRepository(db)


async def get_article_repo(db: AsyncSession = Depends(get_db)) -> ArticleRepository:
    return ArticleRepository(db)


async def get_chat_repo(db: AsyncSession = Depends(get_db)) -> ChatRepository:
    return ChatRepository(db)


async def get_ingestion_repo(db: AsyncSession = Depends(get_db)) -> IngestionRepository:
    return IngestionRepository(db)


async def get_persona_repo(db: AsyncSession = Depends(get_db)) -> PersonaRepository:
    return PersonaRepository(db)


async def get_recommendation_repo(db: AsyncSession = Depends(get_db)) -> RecommendationRepository:
    return RecommendationRepository(db)


async def get_memory_repo(db: AsyncSession = Depends(get_db)) -> MemoryRepository:
    return MemoryRepository(db)
