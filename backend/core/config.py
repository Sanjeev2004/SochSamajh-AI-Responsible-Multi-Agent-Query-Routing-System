from __future__ import annotations

import logging
import os
from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any

logger = logging.getLogger("medical_legal_router")
logger.setLevel(logging.INFO)

class Settings(BaseSettings):
    langsmith_project: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGSMITH_PROJECT", "langsmith_project"),
    )
    langsmith_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGSMITH_API_KEY", "langsmith_api_key"),
    )
    langchain_endpoint: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGCHAIN_ENDPOINT", "langchain_endpoint"),
    )
    
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY", "openai_api_key"),
    )
    openai_model: str = Field(
        default="gpt-4o",
        validation_alias=AliasChoices("OPENAI_MODEL", "openai_model"),
    )
    openai_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_BASE_URL", "openai_base_url"),
    )
    openai_timeout_seconds: float = Field(
        default=20.0,
        validation_alias=AliasChoices("OPENAI_TIMEOUT_SECONDS", "openai_timeout_seconds"),
    )
    openai_max_retries: int = Field(
        default=1,
        validation_alias=AliasChoices("OPENAI_MAX_RETRIES", "openai_max_retries"),
    )
    
    groq_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("GROQ_API_KEY", "groq_api_key"),
    )
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        validation_alias=AliasChoices("GROQ_MODEL", "groq_model"),
    )
    groq_base_url: str = Field(
        default="https://api.groq.com/openai/v1",
        validation_alias=AliasChoices("GROQ_BASE_URL", "groq_base_url"),
    )
    
    enable_llm: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_LLM", "enable_llm"),
    )
    enable_retriever: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_RETRIEVER", "enable_retriever"),
    )
    enable_semantic_router: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_SEMANTIC_ROUTER", "enable_semantic_router"),
    )
    
    llm_fallback_confidence_threshold: float = Field(
        default=0.60,
        validation_alias=AliasChoices("LLM_FALLBACK_CONFIDENCE_THRESHOLD", "llm_fallback_confidence_threshold"),
    )
    
    llm_provider: str = Field(
        default="",
        validation_alias=AliasChoices("LLM_PROVIDER", "llm_provider"),
    )
    backend_cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @field_validator("enable_llm", "enable_retriever", "enable_semantic_router", mode="before")
    @classmethod
    def parse_boolish_env_values(cls, value: Any) -> Any:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "t", "yes", "y", "on"}:
                return True
            if normalized in {"0", "false", "f", "no", "n", "off", "falsey", "falsy"}:
                return False
        return value

    @model_validator(mode="after")
    def setup_provider_and_cors(self) -> Settings:
        # Resolve LLM provider mapping
        requested_provider = self.llm_provider.strip().lower()
        
        # If no provider is explicitly configured, prefer Groq when available.
        if not requested_provider:
            self.llm_provider = "groq" if self.groq_api_key else "openai"
        elif requested_provider in {"openai", "groq"}:
            self.llm_provider = requested_provider
        else:
            self.llm_provider = "groq" if self.groq_api_key else "openai"
            
        if self.llm_provider == "groq":
            self.openai_api_key = self.groq_api_key
            self.openai_model = self.groq_model
            self.openai_base_url = self.groq_base_url
            
        if self.enable_llm and not self.openai_api_key:
            logger.warning(f"ENABLE_LLM is true but {self.llm_provider.upper()} API key is missing.")
            
        # Standardize CORS
        raw_cors = os.getenv("BACKEND_CORS_ORIGINS", "").strip()
        if raw_cors:
            self.backend_cors_origins = [origin.strip() for origin in raw_cors.split(",")]
            
        dev_origins = ["http://localhost:5173", "http://localhost:5174"]
        if "*" not in self.backend_cors_origins:
            for origin in dev_origins:
                if origin not in self.backend_cors_origins:
                    self.backend_cors_origins.append(origin)

        # Set environment variables for LangSmith
        os.environ.setdefault("LANGCHAIN_TRACING_V2", os.getenv("LANGCHAIN_TRACING_V2", "false"))
        if self.langsmith_project:
            os.environ.setdefault("LANGSMITH_PROJECT", self.langsmith_project)
        if self.langsmith_api_key:
            os.environ.setdefault("LANGSMITH_API_KEY", self.langsmith_api_key)
        if self.langchain_endpoint:
            os.environ.setdefault("LANGCHAIN_ENDPOINT", self.langchain_endpoint)

        return self

    @classmethod
    def load(cls) -> "Settings":
        return cls()
