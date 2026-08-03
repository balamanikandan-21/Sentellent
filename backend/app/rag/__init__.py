from app.rag.types import RetrievalResult, SearchFilter

__all__ = ["RAGRetriever", "RetrievalResult", "SearchFilter"]


def __getattr__(name: str):
    # Lazy import: the retriever pulls in the reranker's Anthropic client,
    # which the pure types/confidence scoring don't need.
    if name == "RAGRetriever":
        from app.rag.retriever import RAGRetriever

        return RAGRetriever
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
