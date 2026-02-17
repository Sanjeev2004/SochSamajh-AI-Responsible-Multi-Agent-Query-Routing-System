"""Configuration management for the Medical & Legal Router system.

This module handles loading and validating environment variables,
managing API keys, and providing a singleton Settings object for
use throughout the application.

Example:
    >>> settings = Settings.load()
    >>> print(settings.openrouter_model)
    'openai/gpt-3.5-turbo'
"""
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
    """Immutable configuration container for the application.
    
    All settings are loaded from environment variables and cached
    in a frozen dataclass to prevent accidental modifications.
    
    Attributes:
        openrouter_api_key: API key for OpenRouter LLM provider
        openrouter_model: Model identifier (e.g., 'openai/gpt-3.5-turbo')
        openrouter_base_url: Base URL for OpenRouter API
        openrouter_site_url: Optional site URL for API
        openrouter_app_name: Optional app name for analytics
        langsmith_project: LangSmith project for tracing (optional)
        langsmith_api_key: LangSmith API key for tracing (optional)
        langchain_endpoint: LangChain endpoint (optional)
        backend_cors_origins: List of allowed CORS origins
    """

    langsmith_project: str | None
    langsmith_api_key: str | None
    langchain_endpoint: str | None
    backend_cors_origins: list[str]
    openai_api_key: str | None
    openai_model: str | None


    @staticmethod
    def load() -> "Settings":
        """Load configuration from environment variables.
        
        Loads all configuration values from .env file or environment.
        Provides sensible defaults for optional values.
        Automatically adds localhost to CORS origins for development.
        
        Returns:
            Settings: Frozen dataclass with loaded configuration
            
        Raises:
            Warning: Logged if required OPENROUTER_API_KEY is missing
        """

        langsmith_project = os.getenv("LANGSMITH_PROJECT")
        langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
        langchain_endpoint = os.getenv("LANGCHAIN_ENDPOINT")
        
        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        openai_model = os.getenv("OPENAI_MODEL", "gpt-4o").strip()
        # Parse CORS origins - allow comma-separated string
        cors_origins_str = os.getenv("BACKEND_CORS_ORIGINS", "").strip()
        if cors_origins_str:
            backend_cors_origins = [origin.strip() for origin in cors_origins_str.split(",")]
        else:
            # Default to allow all origins when not specified.
            backend_cors_origins = ["*"]

        # Ensure localhost is allowed for local dev unless using wildcard.
        dev_origins = ["http://localhost:5173", "http://localhost:5174"]
        if "*" not in backend_cors_origins:
            for origin in dev_origins:
                if origin not in backend_cors_origins:
                    backend_cors_origins.append(origin)

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

            langsmith_project=langsmith_project,
            langsmith_api_key=langsmith_api_key,
            langchain_endpoint=langchain_endpoint,
            backend_cors_origins=backend_cors_origins,
            openai_api_key=openai_api_key,
            openai_model=openai_model,
        )
