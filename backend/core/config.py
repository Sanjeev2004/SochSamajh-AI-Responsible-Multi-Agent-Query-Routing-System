from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("medical_legal_router")
logger.setLevel(logging.INFO)


def _clean_env_value(value: str | None, *, remove_all_whitespace: bool = False) -> str:
    if value is None:
        return ""

    cleaned = value.strip().strip("\"'").strip()
    if remove_all_whitespace:
        cleaned = "".join(cleaned.split())
    return cleaned


@dataclass(frozen=True)
class Settings:

    langsmith_project: str | None
    langsmith_api_key: str | None
    langchain_endpoint: str | None
    backend_cors_origins: list[str]
    openai_api_key: str | None
    openai_model: str | None
    openai_base_url: str | None
    openai_timeout_seconds: float
    openai_max_retries: int
    enable_llm: bool
    enable_retriever: bool
    llm_provider: str = "openai"
    enable_semantic_router: bool = False


    @staticmethod
    def load() -> "Settings":

        langsmith_project = os.getenv("LANGSMITH_PROJECT")
        langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        langchain_endpoint = os.getenv("LANGCHAIN_ENDPOINT")
        
        requested_provider = _clean_env_value(os.getenv("LLM_PROVIDER")).lower()
        groq_api_key = _clean_env_value(os.getenv("GROQ_API_KEY"), remove_all_whitespace=True)
        groq_model = _clean_env_value(os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))
        groq_base_url = _clean_env_value(os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"))

        llm_provider = requested_provider or ("groq" if groq_api_key else "openai")
        if llm_provider not in {"openai", "groq"}:
            logger.warning("Unsupported LLM_PROVIDER=%s. Falling back to openai.", llm_provider)
            llm_provider = "openai"
        openai_api_key = _clean_env_value(os.getenv("OPENAI_API_KEY"), remove_all_whitespace=True)
        openai_model = _clean_env_value(os.getenv("OPENAI_MODEL", "gpt-4o"))
        openai_base_url = _clean_env_value(os.getenv("OPENAI_BASE_URL"))

        if llm_provider == "groq":
            openai_api_key = groq_api_key
            openai_model = groq_model
            openai_base_url = groq_base_url

        openai_timeout_seconds = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "20").strip() or "20")
        openai_max_retries = int(os.getenv("OPENAI_MAX_RETRIES", "1").strip() or "1")
        enable_llm = os.getenv("ENABLE_LLM", "false").strip().lower() in {"1", "true", "yes"}
        enable_retriever = os.getenv("ENABLE_RETRIEVER", "false").strip().lower() in {"1", "true", "yes"}
        enable_semantic_router = os.getenv("ENABLE_SEMANTIC_ROUTER", "false").strip().lower() in {"1", "true", "yes"}
        cors_origins_str = os.getenv("BACKEND_CORS_ORIGINS", "").strip()
        if cors_origins_str:
            backend_cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]
        else:
            backend_cors_origins = ["*"]

        dev_origins = ["http://localhost:5173", "http://localhost:5174"]
        if "*" not in backend_cors_origins:
            for origin in dev_origins:
                if origin not in backend_cors_origins:
                    backend_cors_origins.append(origin)

        if enable_llm and not openai_api_key:
            logger.warning(
                "ENABLE_LLM is true but the %s API key is not set. LLM API calls will fail until provided.",
                llm_provider,
            )

        tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2")
        if tracing_enabled is None:
            tracing_enabled = "false"
        os.environ.setdefault("LANGCHAIN_TRACING_V2", tracing_enabled)
        if langsmith_project:
            os.environ.setdefault("LANGSMITH_PROJECT", langsmith_project)
        if langsmith_api_key:
            os.environ.setdefault("LANGSMITH_API_KEY", langsmith_api_key)
        if langchain_endpoint:
            os.environ.setdefault("LANGCHAIN_ENDPOINT", langchain_endpoint)

        return Settings(

            langsmith_project=langsmith_project,
            langsmith_api_key=langsmith_api_key,
            langchain_endpoint=langchain_endpoint,
            backend_cors_origins=backend_cors_origins,
            openai_api_key=openai_api_key,
            openai_model=openai_model,
            openai_base_url=openai_base_url,
            openai_timeout_seconds=openai_timeout_seconds,
            openai_max_retries=openai_max_retries,
            enable_llm=enable_llm,
            enable_retriever=enable_retriever,
            llm_provider=llm_provider,
            enable_semantic_router=enable_semantic_router,
        )
