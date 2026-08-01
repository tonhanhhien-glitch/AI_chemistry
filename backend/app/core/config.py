"""Environment configuration with safe offline defaults."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-latest"
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
    ENABLE_CLAUDE: bool = True
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

