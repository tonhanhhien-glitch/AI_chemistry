"""Environment configuration with safe offline defaults."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL: str = "google/gemma-4-31b-it:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_SITE_URL: str = ""
    OPENROUTER_APP_NAME: str = "QNU VSEPR Learning WebApp"
    # Free-tier models have far less predictable latency than PubChem, so the LLM
    # gets its own budget. generate_explanation() may retry once after a failed
    # validation pass, so the worst case is roughly twice this value -- keep it
    # under half the frontend's /explain timeout.
    OPENROUTER_TIMEOUT_SECONDS: float = 20.0
    # OpenAI is the fallback narrator: it is tried only after OpenRouter fails,
    # so a paid key is spent only when the free tier is down or rate limited.
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_TIMEOUT_SECONDS: float = 20.0
    CORS_ORIGINS: str = "http://localhost:5173"
    PUBCHEM_TIMEOUT_SECONDS: float = 8.0
    PUBCHEM_CACHE_TTL_SECONDS: int = 86400
    PUBCHEM_MAX_REQUESTS_PER_SECOND: float = 4.0
    PUBCHEM_MAX_CANDIDATES: int = 20
    PUBCHEM_RETRY_COUNT: int = 2
    CACHE_DIR: Path = Path("app/cache")
    DATA_DIR: Path = Path("app/runtime_data")
    TEACHER_EXPORT_TOKEN: str = ""
    ENABLE_PUBCHEM: bool = False
    ENABLE_RDKIT: bool = False
    ENABLE_OPENROUTER: bool = False
    ENABLE_OPENAI: bool = False
    MAX_INPUT_LENGTH: int = 80
    LOG_LEVEL: str = "info"

    @property
    def cors_origins_list(self) -> list[str]:
        """Accept comma-separated origins, tolerating an accidental JSON-array value.

        Strips surrounding brackets/quotes so ``["http://localhost:5173"]`` still
        parses to a real origin instead of one malformed entry.
        """

        return [
            origin.strip().strip("[]\"'")
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip().strip("[]\"'")
        ]


settings = Settings()

