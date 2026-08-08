"""Provider fallback: OpenRouter first, OpenAI second, deterministic template last."""

from typing import Any, Callable

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
