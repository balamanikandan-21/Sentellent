from __future__ import annotations

import json

import structlog
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage

from app.config.settings import get_settings
from app.rag.types import RetrievedChunk

logger = structlog.get_logger()

RERANK_PROMPT = """\
You are a relevance judge. Given a user query and a list of text passages, \
score each passage from 0.0 to 1.0 based on how relevant it is to answering the query.

Query: {query}

Passages:
{passages}

Return ONLY a JSON array of scores in the same order as the passages:
[0.85, 0.2, 0.95, ...]
"""


async def rerank_chunks(
    query: str,
    chunks: list[RetrievedChunk],
    top_k: int,
) -> list[RetrievedChunk]:
    if len(chunks) <= top_k:
        for chunk in chunks:
            chunk.rerank_score = chunk.combined_score
        return chunks

    settings = get_settings()
    llm = ChatAnthropic(
        model=settings.TAGGING_MODEL,
        api_key=settings.ANTHROPIC_API_KEY,
        max_tokens=256,
        temperature=0,
    )

    passages_text = "\n\n".join(
        f"[{i}] {chunk.content[:300]}" for i, chunk in enumerate(chunks)
    )

    try:
        response = await llm.ainvoke([
            SystemMessage(content="You score passage relevance. Return only a JSON array."),
            HumanMessage(content=RERANK_PROMPT.format(query=query, passages=passages_text)),
        ])

        raw = response.content if isinstance(response.content, str) else str(response.content)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

        scores = json.loads(raw)

        if isinstance(scores, list) and len(scores) == len(chunks):
            for chunk, score in zip(chunks, scores):
                chunk.rerank_score = float(score)
        else:
            logger.warning("rerank_score_mismatch", expected=len(chunks), got=len(scores) if isinstance(scores, list) else 0)
            for chunk in chunks:
                chunk.rerank_score = chunk.combined_score

    except Exception:
        logger.exception("rerank_failed")
        for chunk in chunks:
            chunk.rerank_score = chunk.combined_score

    chunks.sort(key=lambda c: c.rerank_score or 0, reverse=True)
    result = chunks[:top_k]

    logger.info(
        "reranked",
        input_count=len(chunks),
        output_count=len(result),
        top_score=result[0].rerank_score if result else 0,
    )
    return result
