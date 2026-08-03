from app.memory.types import MemoryEntry, MemoryProfile

__all__ = ["MemoryStore", "MemoryEntry", "MemoryProfile"]


def __getattr__(name: str):
    # Lazy import: the store pulls in the LLM extractor + embeddings client,
    # which the pure types/ranker don't need.
    if name == "MemoryStore":
        from app.memory.store import MemoryStore

        return MemoryStore
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
