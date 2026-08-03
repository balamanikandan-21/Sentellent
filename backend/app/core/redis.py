from redis.asyncio import ConnectionPool, Redis

from app.config.settings import get_settings

_pool: ConnectionPool | None = None


async def get_redis_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        settings = get_settings()
        _pool = ConnectionPool.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
        )
    return _pool


async def get_redis() -> Redis:
    pool = await get_redis_pool()
    return Redis(connection_pool=pool)


async def close_redis() -> None:
    global _pool
    if _pool is not None:
        await _pool.disconnect()
        _pool = None
