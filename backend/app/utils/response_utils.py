"""Consistent stable error-envelope construction."""

from typing import Any


def error_detail(code: str, message: str, **extra: Any) -> dict[str, dict[str, Any]]:
    return {"detail": {"code": code, "message": message, **extra}}
