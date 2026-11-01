"""Shared chat-completions transport with provider fallback.

The LLM is a pedagogical narrator only: every chemistry value it receives is
already immutable. This module therefore does one job -- turn a system prompt
plus messages into text, or raise a sanitized error so callers fall back to the
deterministic templates.

Claude (Anthropic) is tried first, then OpenRouter, then OpenAI. Claude goes
through the official Anthropic SDK; the other two speak the same
``/chat/completions`` dialect, so one request builder covers both. Each provider
is skipped unless its own enable flag and key are set -- any one of them can
therefore run alone.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

import anthropic
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

ProviderName = Literal["anthropic", "openrouter", "openai"]

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
    if settings.ENABLE_ANTHROPIC and settings.ANTHROPIC_API_KEY:
        chain.append(
            _Provider(
                "anthropic",
                settings.ANTHROPIC_API_KEY,
                settings.ANTHROPIC_MODEL,
                "",
                settings.ANTHROPIC_TIMEOUT_SECONDS,
            )
        )
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


# Claude thinks adaptively and thinking counts toward max_tokens, so its cap
# gets headroom on top of the answer budget callers size for the reply itself.
_ANTHROPIC_THINKING_HEADROOM = 2048


def _anthropic_client(provider: _Provider) -> anthropic.Anthropic:
    # No SDK retries: a failure should fall through to the next provider fast,
    # inside the same timeout budget the other providers get.
    return anthropic.Anthropic(api_key=provider.api_key, timeout=provider.timeout, max_retries=0)


def _complete_anthropic(provider: _Provider, system: str, messages: list[dict[str, str]], max_tokens: int) -> str:
    """Call Claude through the Anthropic SDK.

    Sampling parameters are not sent: current Claude models reject them, so
    output determinism comes from the prompt and the downstream validator.
    """

    try:
        response = _anthropic_client(provider).messages.create(
            model=provider.model,
            max_tokens=max_tokens + _ANTHROPIC_THINKING_HEADROOM,
            system=system,
            messages=messages,
            output_config={"effort": settings.ANTHROPIC_EFFORT},
        )
    except anthropic.APITimeoutError as exc:
        logger.warning("anthropic timed out for model %s: %s", provider.model, type(exc).__name__)
        raise LLMError("anthropic_timeout") from exc
    except anthropic.APIStatusError as exc:
        status = exc.status_code
        suffix = _STATUS_REASONS.get(status, "unavailable" if status >= 500 else "request_rejected")
        logger.warning("anthropic HTTP %s for model %s: %.200s", status, provider.model, exc.message)
        raise LLMError(f"anthropic_{suffix}") from exc
    except anthropic.APIConnectionError as exc:
        logger.warning("anthropic transport error: %s", type(exc).__name__)
        raise LLMError("anthropic_unreachable") from exc

    if response.stop_reason == "refusal":
        logger.warning("anthropic declined the request for model %s", provider.model)
        raise LLMError("anthropic_refused")
    # A response can open with thinking blocks, so read text blocks by type.
    text = "".join(block.text for block in response.content if block.type == "text")
    if not text.strip():
        logger.warning("anthropic returned empty content for model %s (stop_reason=%s)", provider.model, response.stop_reason)
        raise LLMError("anthropic_empty_content")
    return text.strip()


def _complete_one(provider: _Provider, system: str, messages: list[dict[str, str]], temperature: float, max_tokens: int) -> str:
    """Call one provider, or raise :class:`LLMError` with a provider-tagged reason.

    Never lets an API key, header dump, or raw provider payload escape: the
    caller turns the reason string into user-visible fallback text.
    """

    if provider.name == "anthropic":
        return _complete_anthropic(provider, system, messages, max_tokens)

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
