"""Pydantic settings loaded from environment variables (API keys, CORS origins, cache paths, timeouts)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ANTHROPIC_API_KEY: str = ""
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    PUBCHEM_TIMEOUT_SECONDS: int = 10
    CACHE_DIR: str = "app/cache"
    LOG_LEVEL: str = "info"


settings = Settings()

