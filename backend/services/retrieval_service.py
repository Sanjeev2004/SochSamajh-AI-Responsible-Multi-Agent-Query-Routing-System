from __future__ import annotations

from core.config import Settings, logger
from core.state import SourceCitation
from agents.retriever import retrieve_context, retrieve_sources


class RetrievalResult:
    def __init__(self, context: str, sources: list[SourceCitation]) -> None:
        self.context = context
        self.sources = sources


def get_retrieved_context(query: str, domain: str, settings: Settings) -> str:
    return get_retrieval_result(query=query, domain=domain, settings=settings).context


def get_retrieval_result(query: str, domain: str, settings: Settings) -> RetrievalResult:
    if not settings.enable_retriever:
        logger.info("Retriever disabled in settings.")
        return RetrievalResult(context="", sources=[])

    sources = retrieve_sources(query=query, domain=domain)
    if sources:
        context = "\n\n".join(f"Source ({source.source}): {source.snippet}" for source in sources)
    else:
        context = retrieve_context(query=query, domain=domain)
    return RetrievalResult(context=context, sources=sources)
