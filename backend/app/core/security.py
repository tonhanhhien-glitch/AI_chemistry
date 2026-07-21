"""Constant-time teacher export-token verification."""

import secrets

from app.core.config import settings


def teacher_token_is_valid(candidate: str) -> bool:
    configured = settings.TEACHER_EXPORT_TOKEN
    return bool(configured and candidate and secrets.compare_digest(candidate, configured))
