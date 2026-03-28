from __future__ import annotations

from core.config import Settings, logger
from agents.retriever import retrieve_context


def get_retrieved_context(query: str, domain: str, settings: Settings) -> str:
    if not settings.enable_retriever:
        logger.info("Retriever disabled in settings.")
        return ""
    return retrieve_context(query=query, domain=domain)
