from __future__ import annotations

from dataclasses import dataclass

import tiktoken


@dataclass
class TextChunk:
    index: int
    content: str
    token_count: int


_encoder: tiktoken.Encoding | None = None


def _get_encoder() -> tiktoken.Encoding:
    global _encoder
    if _encoder is None:
        _encoder = tiktoken.get_encoding("cl100k_base")
    return _encoder


def chunk_text(text: str, *, chunk_size: int = 512, chunk_overlap: int = 64) -> list[TextChunk]:
    encoder = _get_encoder()
    tokens = encoder.encode(text)

    if len(tokens) <= chunk_size:
        return [TextChunk(index=0, content=text, token_count=len(tokens))]

    chunks: list[TextChunk] = []
    start = 0
    idx = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text_str = encoder.decode(chunk_tokens)

        chunks.append(
            TextChunk(
                index=idx,
                content=chunk_text_str,
                token_count=len(chunk_tokens),
            )
        )

        if end >= len(tokens):
            break

        start = end - chunk_overlap
        idx += 1

    return chunks


def count_tokens(text: str) -> int:
    return len(_get_encoder().encode(text))
