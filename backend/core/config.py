from __future__ import annotations

import logging
import os
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any

logger = logging.getLogger("medical_legal_router")
logger.setLevel(logging.INFO)

class Settings(BaseSettings):
    langsmith_project: str | None = Field(default=None, alias="LANGSMITH_PROJECT")
    langsmith_api_key: str | None = Field(default=None, alias="LANGSMITH_API_KEY")
    langchain_endpoint: str | None = Field(default=None, alias="LANGCHAIN_ENDPOINT")
    
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    openai_timeout_seconds: float = Field(default=20.0, alias="OPENAI_TIMEOUT_SECONDS")
    openai_max_retries: int = Field(default=1, alias="OPENAI_MAX_RETRIES")
    
    groq_api_key: str | None = Field(default=None, alias="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_MODEL")
    groq_base_url: str = Field(default="https://api.groq.com/openai/v1", alias="GROQ_BASE_URL")
    
    enable_llm: bool = Field(default=False, alias="ENABLE_LLM")
    enable_retriever: bool = Field(default=False, alias="ENABLE_RETRIEVER")
    enable_semantic_router: bool = Field(default=False, alias="ENABLE_SEMANTIC_ROUTER")
    
    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    backend_cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def setup_provider_and_cors(self) -> Settings:
        # Resolve LLM provider mapping
        requested_provider = self.llm_provider.strip().lower()
        
        # If groq key is provided and no provider specified, default to groq
        if not requested_provider or requested_provider not in {"openai", "groq"}:
            self.llm_provider = "groq" if self.groq_api_key else "openai"
        else:
            self.llm_provider = requested_provider
            
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
