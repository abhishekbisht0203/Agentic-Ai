"""
Application settings and configuration management.

This module provides centralized configuration for all application components
using Pydantic Settings for environment variable management.
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_", extra="ignore")

    user: str = Field(default="airc_user", alias="POSTGRES_USER")
    password: str = Field(default="airc_password", alias="POSTGRES_PASSWORD")
    db: str = Field(default="airc_db", alias="POSTGRES_DB")
    host: str = Field(default="localhost", alias="POSTGRES_HOST")
    port: int = Field(default=5432, alias="POSTGRES_PORT")
    pool_size: int = Field(default=20)
    max_overflow: int = Field(default=30)
    pool_timeout: int = Field(default=30)

    @property
    def database_url(self) -> str:
        """Construct the database connection URL."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.db}"


class RedisSettings(BaseSettings):
    """Redis cache configuration settings."""

    model_config = SettingsConfigDict(env_prefix="REDIS_", extra="ignore")

    host: str = Field(default="localhost", alias="REDIS_HOST")
    port: int = Field(default=6379, alias="REDIS_PORT")
    db: int = Field(default=0, alias="REDIS_DB")
    decode_responses: bool = Field(default=True)
    socket_timeout: int = Field(default=5)

    @property
    def redis_url(self) -> str:
        """Construct the Redis connection URL."""
        return f"redis://{self.host}:{self.port}/{self.db}"


class QdrantSettings(BaseSettings):
    """Qdrant vector database configuration settings."""

    model_config = SettingsConfigDict(env_prefix="QDRANT_", extra="ignore")

    host: str = Field(default="localhost", alias="QDRANT_HOST")
    port: int = Field(default=6333, alias="QDRANT_PORT")
    grpc_port: int = Field(default=6334, alias="QDRANT_GRPC_PORT")
    prefer_grpc: bool = Field(default=False)
    api_key: str | None = Field(default=None)

    @property
    def url(self) -> str:
        """Construct the Qdrant connection URL."""
        return f"http://{self.host}:{self.port}"


class MinIOSettings(BaseSettings):
    """MinIO S3 storage configuration settings."""

    model_config = SettingsConfigDict(env_prefix="MINIO_", extra="ignore")

    endpoint: str = Field(default="localhost:9000", alias="MINIO_ENDPOINT")
    access_key: str = Field(default="airc_admin", alias="MINIO_ROOT_USER")
    secret_key: str = Field(default="airc_password", alias="MINIO_ROOT_PASSWORD")
    bucket_name: str = Field(default="airc-documents", alias="MINIO_BUCKET_NAME")
    secure: bool = Field(default=False, alias="MINIO_SECURE")


class JWTSettings(BaseSettings):
    """JWT authentication configuration settings."""

    model_config = SettingsConfigDict(extra="ignore")

    secret_key: str = Field(default="your-secret-key-change-in-production")
    algorithm: str = Field(default="HS256")
    expiration_hours: int = Field(default=24)
    refresh_expiration_days: int = Field(default=7)
    issuer: str = Field(default="ai-research-copilot")

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate that secret key is long enough for security."""
        if len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters")
        return v


class OAuthSettings(BaseSettings):
    """OAuth provider configuration settings."""

    model_config = SettingsConfigDict(extra="ignore")

    # GitHub OAuth
    github_client_id: str | None = Field(default=None, alias="GITHUB_CLIENT_ID")
    github_client_secret: str | None = Field(default=None, alias="GITHUB_CLIENT_SECRET")

    # Google OAuth
    google_client_id: str | None = Field(default=None, alias="GOOGLE_CLIENT_ID")
    google_client_secret: str | None = Field(default=None, alias="GOOGLE_CLIENT_SECRET")

    # Microsoft OAuth
    microsoft_client_id: str | None = Field(default=None, alias="MICROSOFT_CLIENT_ID")
    microsoft_client_secret: str | None = Field(default=None, alias="MICROSOFT_CLIENT_SECRET")


class LLMProviderSettings(BaseSettings):
    """LLM provider configuration settings."""

    model_config = SettingsConfigDict(extra="ignore")

    # OpenAI
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_default_model: str = Field(default="gpt-4o", alias="OPENAI_DEFAULT_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-3-large", alias="OPENAI_EMBEDDING_MODEL")
    openai_max_tokens: int = Field(default=4096, alias="OPENAI_MAX_TOKENS")
    openai_temperature: float = Field(default=0.7, alias="OPENAI_TEMPERATURE")

    # Anthropic
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_default_model: str = Field(default="claude-3-5-sonnet-20241022", alias="ANTHROPIC_DEFAULT_MODEL")

    # Google Gemini
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    google_default_model: str = Field(default="gemini-2.0-flash-exp", alias="GOOGLE_DEFAULT_MODEL")

    # Ollama (local)
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_default_model: str = Field(default="llama3.3-70b")


class MCPSettings(BaseSettings):
    """MCP (Model Context Protocol) configuration settings."""

    model_config = SettingsConfigDict(env_prefix="MCP_", extra="ignore")

    timeout: int = Field(default=30)
    max_retries: int = Field(default=3)
    registry_path: Path = Field(default_factory=lambda: Path("/app/mcp/servers.json"))


class AppSettings(BaseSettings):
    """Main application configuration settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    name: str = Field(default="AI Research Copilot")
    version: str = Field(default="1.0.0")
    env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="APP_DEBUG")
    log_level: str = Field(default="debug", alias="LOG_LEVEL")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    workers: int = Field(default=4, alias="WORKERS")

    # CORS
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        alias="CORS_ORIGINS"
    )

    # Rate Limiting
    rate_limit_requests: int = Field(default=100, alias="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(default=60, alias="RATE_LIMIT_PERIOD_SECONDS")

    # Feature Flags
    enable_mcp: bool = Field(default=True, alias="ENABLE_MCP")
    enable_rag: bool = Field(default=True, alias="ENABLE_RAG")
    enable_workflows: bool = Field(default=True, alias="ENABLE_WORKFLOWS")
    enable_analytics: bool = Field(default=True, alias="ENABLE_ANALYTICS")

    # Nested settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    qdrant: QdrantSettings = Field(default_factory=QdrantSettings)
    minio: MinIOSettings = Field(default_factory=MinIOSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    oauth: OAuthSettings = Field(default_factory=OAuthSettings)
    llm: LLMProviderSettings = Field(default_factory=LLMProviderSettings)
    mcp: MCPSettings = Field(default_factory=MCPSettings)

    @model_validator(mode="before")
    @classmethod
    def parse_cors_origins(cls, data: Any) -> Any:
        """Parse CORS origins from comma-separated string."""
        if "CORS_ORIGINS" in os.environ and isinstance(data.get("cors_origins"), str):
            data["cors_origins"] = [origin.strip() for origin in data["cors_origins"].split(",")]
        return data


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """
    Get application settings singleton.

    Uses lru_cache to ensure settings are loaded only once.
    """
    return AppSettings()


settings = get_settings()