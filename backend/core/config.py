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
    huggingface_api_token: str
    huggingface_model: str
    langsmith_project: str | None
    langsmith_api_key: str | None
    langchain_endpoint: str | None
    frontend_origin: str


    @staticmethod
    def load() -> "Settings":
        huggingface_api_token = os.getenv("HUGGINGFACEHUB_API_TOKEN", "").strip()
        huggingface_model = os.getenv("HUGGINGFACE_MODEL", "HuggingFaceH4/zephyr-7b-beta").strip()
        langsmith_project = os.getenv("LANGSMITH_PROJECT")
        langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        langchain_endpoint = os.getenv("LANGCHAIN_ENDPOINT")
        frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

        if not huggingface_api_token:
            logger.warning("HUGGINGFACEHUB_API_TOKEN is not set. API calls will fail until provided.")

        os.environ.setdefault("LANGCHAIN_TRACING_V2", os.getenv("LANGCHAIN_TRACING_V2", "true"))
        if langsmith_project:
            os.environ.setdefault("LANGSMITH_PROJECT", langsmith_project)
        if langsmith_api_key:
            os.environ.setdefault("LANGSMITH_API_KEY", langsmith_api_key)
        if langchain_endpoint:
            os.environ.setdefault("LANGCHAIN_ENDPOINT", langchain_endpoint)

        return Settings(
            huggingface_api_token=huggingface_api_token,
            huggingface_model=huggingface_model,
            langsmith_project=langsmith_project,
            langsmith_api_key=langsmith_api_key,
            langchain_endpoint=langchain_endpoint,
            frontend_origin=frontend_origin,
        )
