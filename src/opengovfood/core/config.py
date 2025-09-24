from __future__ import annotations

from functools import lru_cache
from typing import List, Optional, Union

from pydantic import AnyHttpUrl, ConfigDict, EmailStr, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "OpenGov Food"
    APP_NAME: str = "OpenGov Food"
    APP_VERSION: str = "1.0.0"
    SECRET_KEY: str = "a-secret-key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    DEBUG: bool = False
    DB_ECHO: bool = False
    SERVER_NAME: str = "OpenGovFood"
    SERVER_HOST: AnyHttpUrl = "http://localhost"

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "opengovfood"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: Optional[AnyHttpUrl] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, value: Optional[str]) -> str:
        if isinstance(value, str) and value:
            return value
        return "sqlite+aiosqlite:///./opengovfood.db"

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(
        cls, value: Union[str, List[str]]
    ) -> Union[List[str], str]:
        if isinstance(value, str) and not value.startswith("["):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, (list, str)):
            return value
        raise ValueError(value)

    # Users
    FIRST_SUPERUSER: EmailStr = "admin@opengovfood.com"
    FIRST_SUPERUSER_PASSWORD: str = "password"
    USERS_OPEN_REGISTRATION: bool = True

    model_config = ConfigDict(case_sensitive=True, env_file=".env")

    @property
    def database_url(self) -> str:
        """Return the SQLAlchemy database URL."""
        return self.SQLALCHEMY_DATABASE_URI or "sqlite+aiosqlite:///./opengovfood.db"

    @property
    def openai_api_key(self) -> Optional[str]:
        """Return the configured OpenAI API key if present."""
        return self.OPENAI_API_KEY

    @property
    def ollama_base_url(self) -> Optional[str]:
        """Return the configured Ollama base URL with sensible default."""
        if self.OLLAMA_BASE_URL:
            return str(self.OLLAMA_BASE_URL)
        return "http://localhost:11434"


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""
    return Settings()


settings = get_settings()