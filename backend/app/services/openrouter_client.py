"""Shared OpenRouter chat-completions transport.

The LLM is a pedagogical narrator only: every chemistry value it receives is
already immutable. This module therefore does one job -- turn a system prompt
plus messages into text, or raise a sanitized error so callers fall back to the
deterministic templates.
"""

import logging
from typing import Any

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_STATUS_REASONS = {
    401: "openrouter_unauthorized",
    402: "openrouter_insufficient_credits",
    403: "openrouter_forbidden",
    404: "openrouter_model_not_found",
    429: "openrouter_rate_limited",
}


class OpenRouterError(RuntimeError):
    """Sanitized failure; the message is safe to surface as a fallback reason."""


def is_configured() -> bool:
    return bool(settings.ENABLE_OPENROUTER and settings.OPENROUTER_API_KEY)


def _headers() -> dict[str, str]:
    headers = {"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}", "Content-Type": "application/json"}
    if settings.OPENROUTER_SITE_URL:
        headers["HTTP-Referer"] = settings.OPENROUTER_SITE_URL
    if settings.OPENROUTER_APP_NAME:
        headers["X-OpenRouter-Title"] = settings.OPENROUTER_APP_NAME
    return headers


def complete(system: str, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> str:
    """Return the assistant text, or raise :class:`OpenRouterError`.

    Never lets an API key, header dump, or raw provider payload escape: the
    caller turns the reason string into user-visible fallback text.
    """

    payload: dict[str, Any] = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [{"role": "system", "content": system}, *messages],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    url = f"{settings.OPENROUTER_BASE_URL.rstrip('/')}/chat/completions"
    try:
        with httpx.Client(timeout=settings.OPENROUTER_TIMEOUT_SECONDS) as client:
            response = client.post(url, headers=_headers(), json=payload)
            response.raise_for_status()
            body = response.json()
    except httpx.TimeoutException as exc:
        logger.warning("OpenRouter timed out for model %s: %s", settings.OPENROUTER_MODEL, type(exc).__name__)
        raise OpenRouterError("openrouter_timeout") from exc
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        reason = _STATUS_REASONS.get(status, "openrouter_unavailable" if status >= 500 else "openrouter_request_rejected")
        # Body may echo provider detail; log truncated and never return it upstream.
        logger.warning("OpenRouter HTTP %s for model %s: %.200s", status, settings.OPENROUTER_MODEL, exc.response.text)
        raise OpenRouterError(reason) from exc
    except httpx.HTTPError as exc:
        logger.warning("OpenRouter transport error: %s", type(exc).__name__)
        raise OpenRouterError("openrouter_unreachable") from exc
    except ValueError as exc:
        logger.warning("OpenRouter returned a non-JSON body for model %s", settings.OPENROUTER_MODEL)
        raise OpenRouterError("openrouter_invalid_response") from exc

    if isinstance(body, dict) and body.get("error"):
        logger.warning("OpenRouter error envelope for model %s: %.200s", settings.OPENROUTER_MODEL, body["error"])
        raise OpenRouterError("openrouter_provider_error")
    choices = body.get("choices") if isinstance(body, dict) else None
    if not choices:
        logger.warning("OpenRouter returned no choices for model %s", settings.OPENROUTER_MODEL)
        raise OpenRouterError("openrouter_empty_choices")
    text = ((choices[0] or {}).get("message") or {}).get("content") or ""
    if not text.strip():
        logger.warning("OpenRouter returned empty content for model %s", settings.OPENROUTER_MODEL)
        raise OpenRouterError("openrouter_empty_content")
    return text.strip()
