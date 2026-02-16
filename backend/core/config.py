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
    openrouter_api_key: str
    openrouter_model: str
    openrouter_base_url: str
    openrouter_site_url: str | None
    openrouter_app_name: str | None
    langsmith_project: str | None
    langsmith_api_key: str | None
    langchain_endpoint: str | None
    backend_cors_origins: list[str]


    @staticmethod
    def load() -> "Settings":
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        openrouter_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-20b:free").strip()
        openrouter_base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()
        openrouter_site_url = os.getenv("OPENROUTER_SITE_URL", "").strip() or None
        openrouter_app_name = os.getenv("OPENROUTER_APP_NAME", "").strip() or None
        langsmith_project = os.getenv("LANGSMITH_PROJECT")
        langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        langchain_endpoint = os.getenv("LANGCHAIN_ENDPOINT")
        # Parse CORS origins - allow comma-separated string
        cors_origins_str = os.getenv("BACKEND_CORS_ORIGINS", "").strip()
        if cors_origins_str:
            backend_cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]
        else:
            # Default to allow all origins when not specified.
            backend_cors_origins = ["*"]

        # Ensure localhost is allowed for local dev unless using wildcard.
        if "*" not in backend_cors_origins and "http://localhost:5173" not in backend_cors_origins:
            backend_cors_origins.append("http://localhost:5173")

        if not openrouter_api_key:
            logger.warning("OPENROUTER_API_KEY is not set. API calls will fail until provided.")

        os.environ.setdefault("LANGCHAIN_TRACING_V2", os.getenv("LANGCHAIN_TRACING_V2", "true"))
        if langsmith_project:
            os.environ.setdefault("LANGSMITH_PROJECT", langsmith_project)
        if langsmith_api_key:
            os.environ.setdefault("LANGSMITH_API_KEY", langsmith_api_key)
        if langchain_endpoint:
            os.environ.setdefault("LANGCHAIN_ENDPOINT", langchain_endpoint)

        return Settings(
            openrouter_api_key=openrouter_api_key,
            openrouter_model=openrouter_model,
            openrouter_base_url=openrouter_base_url,
            openrouter_site_url=openrouter_site_url,
            openrouter_app_name=openrouter_app_name,
            langsmith_project=langsmith_project,
            langsmith_api_key=langsmith_api_key,
            langchain_endpoint=langchain_endpoint,
            backend_cors_origins=backend_cors_origins,
        )
