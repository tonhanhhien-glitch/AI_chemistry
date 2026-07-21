"""Environment configuration with safe offline defaults."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-haiku-latest"
    CORS_ORIGINS: str = "http://localhost:5173"
    PUBCHEM_TIMEOUT_SECONDS: float = 8.0
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
        """Accept comma-separated origins and strip accidental whitespace."""

        return [
            origin.strip()
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()

