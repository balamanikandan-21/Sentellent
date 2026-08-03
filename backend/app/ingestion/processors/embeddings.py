from __future__ import annotations

import asyncio

import structlog
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config.settings import get_settings

logger = structlog.get_logger()

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        settings = get_settings()
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=15),
    reraise=True,
)
def _embed_batch_sync(texts: list[str], model: str, dimensions: int) -> list[list[float]]:
    client = _get_client()
    response = client.embeddings.create(
        input=texts,
        model=model,
        dimensions=dimensions,
    )
    sorted_data = sorted(response.data, key=lambda x: x.index)
    return [d.embedding for d in sorted_data]


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    settings = get_settings()
    model = settings.EMBEDDING_MODEL
    dimensions = settings.EMBEDDING_DIMENSIONS
    batch_size = settings.EMBEDDING_BATCH_SIZE

    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        logger.debug("embedding_batch", batch_index=i // batch_size, size=len(batch))
        embeddings = await asyncio.to_thread(
            _embed_batch_sync, batch, model, dimensions
        )
        all_embeddings.extend(embeddings)

    logger.info("embeddings_generated", count=len(all_embeddings))
    return all_embeddings


async def generate_single_embedding(text: str) -> list[float]:
    results = await generate_embeddings([text])
    return results[0]
