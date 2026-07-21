"""Offline integration degradation, ambiguity, and explanation contradiction tests."""

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.core.config import settings
from app.core.exceptions import AmbiguousMoleculeError
from app.main import app
from app.services import molecule_resolver
from app.services.formula_parser import parse_formula
from app.services.pubchem_service import lookup_pubchem
from app.services.rdkit_service import generate_rdkit_molblock
from app.services.validation_service import validate_explanation_text

client = TestClient(app)


def test_optional_integrations_are_offline_safe(tmp_path: Path) -> None:
    old_cache, old_pubchem, old_rdkit = settings.CACHE_DIR, settings.ENABLE_PUBCHEM, settings.ENABLE_RDKIT
    settings.CACHE_DIR = tmp_path; settings.ENABLE_PUBCHEM = False; settings.ENABLE_RDKIT = False
    try:
        (tmp_path / "pubchem_cache.json").write_text("{corrupt", encoding="utf-8")
        assert lookup_pubchem("water") == []
        assert generate_rdkit_molblock("O") is None
    finally:
        settings.CACHE_DIR, settings.ENABLE_PUBCHEM, settings.ENABLE_RDKIT = old_cache, old_pubchem, old_rdkit


def test_ambiguous_resolution_returns_candidates(monkeypatch: pytest.MonkeyPatch) -> None:
    first = deepcopy(molecule_resolver.curated_records()[0]); second = deepcopy(first); second["id"] = "co2-isomer-candidate"; second["name_vi"] = "Ứng viên khác"
    monkeypatch.setattr(molecule_resolver, "curated_records", lambda: (first, second))
    with pytest.raises(AmbiguousMoleculeError) as caught:
        molecule_resolver.resolve_molecule(parse_formula("CO2"))
    assert len(caught.value.candidates or []) == 2


def test_ambiguity_api_envelope(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import analysis_service
    error = AmbiguousMoleculeError([{"id": "a", "formula": "C2H6O", "name_vi": "A"}])
    monkeypatch.setattr(analysis_service, "resolve_molecule", lambda *_args, **_kwargs: (_ for _ in ()).throw(error))
    response = client.post("/api/v1/analyze", json={"formula": "CO2"})
    assert response.status_code == 409
    assert response.json()["detail"]["candidates"][0]["id"] == "a"


def test_explanation_contradictions_are_detected() -> None:
    record = molecule_resolver.get_record("h2o")
    valid, problems = validate_explanation_text("H2O được ghi AX2E2, bent, tetrahedral, góc 104.5°.", record)
    assert valid and not problems
    valid, problems = validate_explanation_text("H2O được ghi AX4, linear, góc 180°.", record)
    assert not valid
    assert {"contradictory_ax_en", "contradictory_geometry", "contradictory_angle"}.issubset(problems)
