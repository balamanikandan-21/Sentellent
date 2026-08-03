from __future__ import annotations

import re
from dataclasses import dataclass

import tiktoken

_encoder: tiktoken.Encoding | None = None
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z])")


def _get_encoder() -> tiktoken.Encoding:
    global _encoder
    if _encoder is None:
        _encoder = tiktoken.get_encoding("cl100k_base")
    return _encoder


@dataclass
class EnrichedChunk:
    index: int
    content: str
    token_count: int
    header: str


def chunk_with_context(
    text: str,
    *,
    title: str = "",
    source: str = "",
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> list[EnrichedChunk]:
    """Sentence-aware chunking that preserves boundaries and prepends metadata."""
    encoder = _get_encoder()
    header = ""
    if title:
        header += f"Title: {title}"
    if source:
        header += f" | Source: {source}" if header else f"Source: {source}"

    sentences = _SENTENCE_SPLIT.split(text.strip())
    if not sentences:
        return []

    chunks: list[EnrichedChunk] = []
    current_sentences: list[str] = []
    current_tokens = 0
    header_tokens = len(encoder.encode(header + "\n\n")) if header else 0
    budget = chunk_size - header_tokens
    idx = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        sent_tokens = len(encoder.encode(sentence + " "))

        if current_tokens + sent_tokens > budget and current_sentences:
            chunk_text = " ".join(current_sentences)
            full_text = f"{header}\n\n{chunk_text}" if header else chunk_text
            chunks.append(EnrichedChunk(
                index=idx,
                content=full_text,
                token_count=len(encoder.encode(full_text)),
                header=header,
            ))
            idx += 1

            overlap_tokens = 0
            overlap_sentences: list[str] = []
            for s in reversed(current_sentences):
                s_tok = len(encoder.encode(s + " "))
                if overlap_tokens + s_tok > chunk_overlap:
                    break
                overlap_sentences.insert(0, s)
                overlap_tokens += s_tok

            current_sentences = overlap_sentences
            current_tokens = overlap_tokens

        current_sentences.append(sentence)
        current_tokens += sent_tokens

    if current_sentences:
        chunk_text = " ".join(current_sentences)
        full_text = f"{header}\n\n{chunk_text}" if header else chunk_text
        chunks.append(EnrichedChunk(
            index=idx,
            content=full_text,
            token_count=len(encoder.encode(full_text)),
            header=header,
        ))

    if not chunks:
        tokens = encoder.encode(text[:2000])
        full_text = f"{header}\n\n{text[:2000]}" if header else text[:2000]
        chunks.append(EnrichedChunk(
            index=0,
            content=full_text,
            token_count=len(tokens),
            header=header,
        ))

    return chunks
