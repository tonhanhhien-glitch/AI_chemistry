"""Dependency helpers kept side-effect free for tests and OpenAPI routes."""

from app.core.config import Settings, settings


def get_settings() -> Settings:
    return settings
