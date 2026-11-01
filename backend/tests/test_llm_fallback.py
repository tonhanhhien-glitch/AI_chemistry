"""Provider fallback: Claude first, OpenRouter second, OpenAI third, deterministic template last."""

from types import SimpleNamespace
from typing import Any, Callable

import anthropic
import httpx
import pytest

from app.core.config import settings
from app.schemas.chat_schema import ChatMessage
from app.services import chat_service, llm_client, molecule_resolver


def _reply(text: str) -> httpx.Response:
    return httpx.Response(200, json={"choices": [{"message": {"content": text}}]})


def _route(monkeypatch: pytest.MonkeyPatch, handler: Callable[[httpx.Request], httpx.Response]) -> list[httpx.Request]:
    """Serve both providers from an in-memory transport and record every request."""

    seen: list[httpx.Request] = []
    real_client = httpx.Client

    def recording(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    def factory(*args: Any, **kwargs: Any) -> httpx.Client:
        return real_client(*args, transport=httpx.MockTransport(recording), **kwargs)

    monkeypatch.setattr(llm_client.httpx, "Client", factory)
    return seen


def _enable(monkeypatch: pytest.MonkeyPatch, openrouter: bool = True, openai: bool = True) -> None:
    monkeypatch.setattr(settings, "ENABLE_OPENROUTER", openrouter)
    monkeypatch.setattr(settings, "ENABLE_OPENAI", openai)
    monkeypatch.setattr(settings, "OPENROUTER_API_KEY", "test-openrouter-key")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setattr(settings, "OPENAI_MODEL", "gpt-4o-mini")


def test_openrouter_answers_without_touching_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable(monkeypatch)
    seen = _route(monkeypatch, lambda _request: _reply("from openrouter"))
    completion = llm_client.complete("rules", [{"role": "user", "content": "hi"}], temperature=0, max_tokens=10)
    assert (completion.provider, completion.text) == ("openrouter", "from openrouter")
    assert [request.url.host for request in seen] == ["openrouter.ai"]


def test_openai_takes_over_when_openrouter_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable(monkeypatch)
    seen = _route(monkeypatch, lambda request: _reply("from openai") if request.url.host == "api.openai.com" else httpx.Response(429, text="rate limited"))
    completion = llm_client.complete("rules", [{"role": "user", "content": "hi"}], temperature=0, max_tokens=10)
    assert (completion.provider, completion.text) == ("openai", "from openai")
    assert [request.url.host for request in seen] == ["openrouter.ai", "api.openai.com"]
    fallback = seen[1]
    assert fallback.headers["Authorization"] == "Bearer test-openai-key"
    assert b'"gpt-4o-mini"' in fallback.content


def test_openai_serves_alone_when_openrouter_is_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable(monkeypatch, openrouter=False)
    seen = _route(monkeypatch, lambda _request: _reply("only openai"))
    assert llm_client.is_configured()
    assert llm_client.complete("rules", [{"role": "user", "content": "hi"}], temperature=0, max_tokens=10).provider == "openai"
    assert [request.url.host for request in seen] == ["api.openai.com"]


def test_chat_falls_back_to_template_when_both_providers_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable(monkeypatch)
    _route(monkeypatch, lambda _request: httpx.Response(500, text="upstream exploded"))
    response = chat_service.generate_chat_reply(molecule_resolver.get_record("h2o"), [ChatMessage(role="user", content="Góc liên kết?")], "vi")
    assert response.source == "deterministic_fallback"
    # Both attempts are reported, and neither key nor provider body escapes.
    assert response.fallback_reason == "openrouter_unavailable; openai_unavailable"


def test_unconfigured_chain_is_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable(monkeypatch, openrouter=False, openai=False)
    assert not llm_client.is_configured()
    with pytest.raises(llm_client.LLMError, match="llm_not_configured"):
        llm_client.complete("rules", [{"role": "user", "content": "hi"}], temperature=0, max_tokens=10)


class _FakeClaude:
    """Stands in for ``anthropic.Anthropic``; records every create() call."""

    def __init__(self, respond: Callable[[dict[str, Any]], Any]) -> None:
        self.calls: list[dict[str, Any]] = []
        self._respond = respond
        self.messages = self

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self._respond(kwargs)


def _claude_message(text: str, stop_reason: str = "end_turn") -> SimpleNamespace:
    # A thinking block first, as Claude Haiku 5.5 can return, so the text must be found by type.
    blocks = [SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text=text)]
    return SimpleNamespace(content=blocks, stop_reason=stop_reason)


def _enable_claude(monkeypatch: pytest.MonkeyPatch, fake: _FakeClaude) -> None:
    monkeypatch.setattr(settings, "ENABLE_ANTHROPIC", True)
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setattr(settings, "ANTHROPIC_MODEL", "claude-haiku-5-5")
    monkeypatch.setattr(llm_client, "_anthropic_client", lambda _provider: fake)


def test_claude_answers_first_without_touching_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable(monkeypatch)
    fake = _FakeClaude(lambda _kwargs: _claude_message("from claude"))
    _enable_claude(monkeypatch, fake)
    seen = _route(monkeypatch, lambda _request: _reply("should not be used"))
    completion = llm_client.complete("rules", [{"role": "user", "content": "hi"}], temperature=0.2, max_tokens=10)
    assert (completion.provider, completion.text) == ("anthropic", "from claude")
    assert seen == []
    call = fake.calls[0]
    assert call["model"] == "claude-haiku-5-5"
    assert call["system"] == "rules"
    # Sampling parameters are rejected by current Claude models, so none are sent.
    assert "temperature" not in call
    assert llm_client.model_fingerprint().startswith("anthropic:claude-haiku-5-5,")


def test_openrouter_takes_over_when_claude_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable(monkeypatch)

    def overloaded(_kwargs: dict[str, Any]) -> Any:
        request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        raise anthropic.RateLimitError("rate limited", response=httpx.Response(429, request=request), body=None)

    _enable_claude(monkeypatch, _FakeClaude(overloaded))
    seen = _route(monkeypatch, lambda _request: _reply("from openrouter"))
    completion = llm_client.complete("rules", [{"role": "user", "content": "hi"}], temperature=0, max_tokens=10)
    assert (completion.provider, completion.text) == ("openrouter", "from openrouter")
    assert [request.url.host for request in seen] == ["openrouter.ai"]


def test_claude_refusal_is_a_sanitized_fallback_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    _enable(monkeypatch, openrouter=False, openai=False)
    _enable_claude(monkeypatch, _FakeClaude(lambda _kwargs: _claude_message("", stop_reason="refusal")))
    with pytest.raises(llm_client.LLMError, match="^anthropic_refused$"):
        llm_client.complete("rules", [{"role": "user", "content": "hi"}], temperature=0, max_tokens=10)
