from __future__ import annotations

from dataclasses import dataclass, field
from langsmith import traceable

from core.config import Settings, logger
from core.state import SourceCitation
from agents.retriever import retrieve_context, retrieve_sources

@dataclass(frozen=True)
class RetrievalResult:
    context: str
    sources: list[SourceCitation] = field(default_factory=list)


@traceable(name="retrieval_service_context")
def get_retrieved_context(query: str, domain: str, settings: Settings) -> str:
    return get_retrieval_result(query=query, domain=domain, settings=settings).context


@traceable(name="retrieval_service")
def get_retrieval_result(query: str, domain: str, settings: Settings) -> RetrievalResult:
    if not settings.enable_retriever:
        logger.info("Retriever disabled in settings. Skipping search.")
        return RetrievalResult(context="", sources=[])

    try:
        sources = retrieve_sources(query=query, domain=domain)
        if sources:
            context = "\n\n".join(f"Source ({source.source}): {source.snippet}" for source in sources)
            logger.info("Retrieved %d sources for domain '%s'", len(sources), domain)
        else:
            context = retrieve_context(query=query, domain=domain)
            logger.info("Retrieved text context for domain '%s'", domain)
            
        return RetrievalResult(context=context, sources=sources)
        
    except Exception as exc:
        logger.error("Vector database retrieval failed for domain '%s': %s", domain, exc, exc_info=True)
        # Fail securely without crashing the router pipeline
        return RetrievalResult(context="", sources=[])
