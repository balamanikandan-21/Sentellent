from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/sentellent"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    REDIS_URL: str = "redis://localhost:6379/0"

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/api/v1/auth/google/callback"
    JWT_SECRET_KEY: str = "dev-only-change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 10080

    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    PRIMARY_MODEL: str = "claude-sonnet-5"
    TAGGING_MODEL: str = "claude-haiku-4-5"
    LLM_MAX_TOKENS: int = 1536
    LLM_TEMPERATURE: float = 0.3
    RAG_TOP_K: int = 8
    RAG_CANDIDATE_K: int = 25
    RAG_RERANK_K: int = 6
    HYBRID_ALPHA: float = 0.7
    CONFIDENCE_THRESHOLD: float = 0.35
    CHAT_HISTORY_LIMIT: int = 20
    MEMORY_TOP_K: int = 10
    MEMORY_SIMILARITY_THRESHOLD: float = 0.3
    MEMORY_DECAY_DAYS: int = 90

    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSIONS: int = 1536
    EMBEDDING_BATCH_SIZE: int = 20
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    MAX_ARTICLES_PER_FEED: int = 50
    INGESTION_RETRY_ATTEMPTS: int = 3

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    FRONTEND_URL: str = "http://localhost:3000"

    APP_NAME: str = "Sentellent Stock Analyst"
    API_V1_PREFIX: str = "/api/v1"

    @property
    def async_database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            missing = []
            if not self.GOOGLE_CLIENT_ID:
                missing.append("GOOGLE_CLIENT_ID")
            if not self.GOOGLE_CLIENT_SECRET:
                missing.append("GOOGLE_CLIENT_SECRET")
            if self.JWT_SECRET_KEY == "dev-only-change-me":
                missing.append("JWT_SECRET_KEY")
            if not self.ANTHROPIC_API_KEY:
                missing.append("ANTHROPIC_API_KEY")
            if not self.OPENAI_API_KEY:
                missing.append("OPENAI_API_KEY")
            if missing:
                raise ValueError(f"Production requires: {', '.join(missing)}")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
