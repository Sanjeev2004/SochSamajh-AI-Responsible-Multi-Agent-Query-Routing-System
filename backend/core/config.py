from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("medical_legal_router")
logger.setLevel(logging.INFO)


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    langsmith_project: str | None
    langsmith_api_key: str | None
    langchain_endpoint: str | None
    backend_cors_origins: list[str]


    @staticmethod
    def load() -> "Settings":
        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()
        langsmith_project = os.getenv("LANGSMITH_PROJECT")
        langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        langchain_endpoint = os.getenv("LANGCHAIN_ENDPOINT")
        # Parse CORS origins - allow comma-separated string
        cors_origins_str = os.getenv("BACKEND_CORS_ORIGINS", "")
        if cors_origins_str:
            backend_cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]
        else:
            # Fallback to legacy FRONTEND_ORIGIN or default
            backend_cors_origins = [os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")]

        # Always ensure localhost:5173 is allowed for local dev if not present (optional, but good for safety)
        if "http://localhost:5173" not in backend_cors_origins:
            backend_cors_origins.append("http://localhost:5173")

        if not openai_api_key:
            logger.warning("OPENAI_API_KEY is not set. API calls will fail until provided.")

        os.environ.setdefault("LANGCHAIN_TRACING_V2", os.getenv("LANGCHAIN_TRACING_V2", "true"))
        if langsmith_project:
            os.environ.setdefault("LANGSMITH_PROJECT", langsmith_project)
        if langsmith_api_key:
            os.environ.setdefault("LANGSMITH_API_KEY", langsmith_api_key)
        if langchain_endpoint:
            os.environ.setdefault("LANGCHAIN_ENDPOINT", langchain_endpoint)

        return Settings(
            openai_api_key=openai_api_key,
            openai_model=openai_model,
            langsmith_project=langsmith_project,
            langsmith_api_key=langsmith_api_key,
            langchain_endpoint=langchain_endpoint,
            backend_cors_origins=backend_cors_origins,
        )
