"""Shared chat-completions transport with provider fallback.

The LLM is a pedagogical narrator only: every chemistry value it receives is
already immutable. This module therefore does one job -- turn a system prompt
plus messages into text, or raise a sanitized error so callers fall back to the
deterministic templates.

OpenRouter is tried first and OpenAI second, so the paid key is spent only when
the free tier is down, rate limited, or out of credit. Both speak the same
``/chat/completions`` dialect, so one request builder covers both, and each
provider is skipped unless its own enable flag and key are set -- either one can
therefore run alone.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

ProviderName = Literal["openrouter", "openai"]

# Suffixes are provider-prefixed before they leave this module, so a fallback
# reason always names the provider that produced it.
_STATUS_REASONS = {
    401: "unauthorized",
    402: "insufficient_credits",
    403: "forbidden",
    404: "model_not_found",
    429: "rate_limited",
}


class LLMError(RuntimeError):
    """Sanitized failure; the message is safe to surface as a fallback reason."""


@dataclass(frozen=True)
class _Provider:
    name: ProviderName
    api_key: str
    model: str
    base_url: str
    timeout: float
    extra_headers: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMCompletion:
    """Assistant text plus the provider that actually answered."""

    text: str
    provider: ProviderName


def _providers() -> list[_Provider]:
    """Return the enabled providers in fallback order (may be empty)."""

    chain: list[_Provider] = []
    if settings.ENABLE_OPENROUTER and settings.OPENROUTER_API_KEY:
        headers: dict[str, str] = {}
        if settings.OPENROUTER_SITE_URL:
            headers["HTTP-Referer"] = settings.OPENROUTER_SITE_URL
        if settings.OPENROUTER_APP_NAME:
            headers["X-OpenRouter-Title"] = settings.OPENROUTER_APP_NAME
        chain.append(
            _Provider(
                "openrouter",
                settings.OPENROUTER_API_KEY,
                settings.OPENROUTER_MODEL,
                settings.OPENROUTER_BASE_URL,
                settings.OPENROUTER_TIMEOUT_SECONDS,
                headers,
            )
        )
    if settings.ENABLE_OPENAI and settings.OPENAI_API_KEY:
        chain.append(
            _Provider(
                "openai",
                settings.OPENAI_API_KEY,
                settings.OPENAI_MODEL,
                settings.OPENAI_BASE_URL,
                settings.OPENAI_TIMEOUT_SECONDS,
            )
        )
    return chain


def is_configured() -> bool:
    return bool(_providers())


def model_fingerprint() -> str:
    """Identify the active chain so caches invalidate when a model changes."""

    return ",".join(f"{provider.name}:{provider.model}" for provider in _providers())


def _complete_one(provider: _Provider, system: str, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> str:
    """Call one provider, or raise :class:`LLMError` with a provider-tagged reason.

    Never lets an API key, header dump, or raw provider payload escape: the
    caller turns the reason string into user-visible fallback text.
    """

    payload: dict[str, Any] = {
        "model": provider.model,
        "messages": [{"role": "system", "content": system}, *messages],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {"Authorization": f"Bearer {provider.api_key}", "Content-Type": "application/json", **provider.extra_headers}
    url = f"{provider.base_url.rstrip('/')}/chat/completions"
    try:
        with httpx.Client(timeout=provider.timeout) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            body = response.json()
    except httpx.TimeoutException as exc:
        logger.warning("%s timed out for model %s: %s", provider.name, provider.model, type(exc).__name__)
        raise LLMError(f"{provider.name}_timeout") from exc
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        suffix = _STATUS_REASONS.get(status, "unavailable" if status >= 500 else "request_rejected")
        # Body may echo provider detail; log truncated and never return it upstream.
        logger.warning("%s HTTP %s for model %s: %.200s", provider.name, status, provider.model, exc.response.text)
        raise LLMError(f"{provider.name}_{suffix}") from exc
    except httpx.HTTPError as exc:
        logger.warning("%s transport error: %s", provider.name, type(exc).__name__)
        raise LLMError(f"{provider.name}_unreachable") from exc
    except ValueError as exc:
        logger.warning("%s returned a non-JSON body for model %s", provider.name, provider.model)
        raise LLMError(f"{provider.name}_invalid_response") from exc

    if isinstance(body, dict) and body.get("error"):
        logger.warning("%s error envelope for model %s: %.200s", provider.name, provider.model, body["error"])
        raise LLMError(f"{provider.name}_provider_error")
    choices = body.get("choices") if isinstance(body, dict) else None
    if not choices:
        logger.warning("%s returned no choices for model %s", provider.name, provider.model)
        raise LLMError(f"{provider.name}_empty_choices")
    text = ((choices[0] or {}).get("message") or {}).get("content") or ""
    if not text.strip():
        logger.warning("%s returned empty content for model %s", provider.name, provider.model)
        raise LLMError(f"{provider.name}_empty_content")
    return text.strip()


def complete(system: str, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> LLMCompletion:
    """Return the first provider's answer, falling back down the chain.

    Every provider failure is sanitized, so the raised message lists only reason
    codes -- one per attempted provider -- and stays safe to show as fallback text.
    """

    chain = _providers()
    if not chain:
        raise LLMError("llm_not_configured")
    reasons: list[str] = []
    for provider in chain:
        try:
            return LLMCompletion(_complete_one(provider, system, messages, temperature, max_tokens), provider.name)
        except LLMError as exc:
            reasons.append(str(exc))
    raise LLMError("; ".join(reasons))
