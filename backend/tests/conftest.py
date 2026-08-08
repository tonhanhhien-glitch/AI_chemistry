"""Keep the suite deterministic and offline by default."""

import pytest

from app.core.config import settings

_EXTERNAL_FLAGS = ("ENABLE_PUBCHEM", "ENABLE_RDKIT", "ENABLE_OPENROUTER", "ENABLE_OPENAI")


@pytest.fixture(autouse=True)
def _external_services_off(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable every external integration unless a test opts back in.

    Settings are loaded from ``.env``, so a developer holding real credentials
    would otherwise run the suite against live PubChem, OpenRouter, and OpenAI. The
    ``*_offline`` assertions would then pass or fail depending on whether the
    network happened to fail inside the timeout. Tests that exercise an external
    path re-enable the flag they need with their own monkeypatch, which is
    applied after this fixture and therefore wins.
    """

    for flag in _EXTERNAL_FLAGS:
        monkeypatch.setattr(settings, flag, False)
