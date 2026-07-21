"""Success/error schema coverage for the mounted v1 routes."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_analyze_success_offline() -> None:
    response = client.post("/api/v1/analyze", json={"formula": "H2O", "include_explanation": True})
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "1.0"
    assert body["vsepr"]["ax_en"] == "AX2E2"
    assert body["lewis"]["total_valence_electrons"] == 8
    assert body["structure3d"]["is_illustrative"] is True
    assert body["explanation"]["source"] == "deterministic_fallback"


def test_analyze_unsupported_is_structured() -> None:
    response = client.post("/api/v1/analyze", json={"formula": "H2"})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "UNSUPPORTED_MOLECULE"


def test_examples_search_rules_and_explain() -> None:
    examples = client.get("/api/v1/molecules/examples")
    assert examples.status_code == 200
    assert len(examples.json()) >= 15
    search = client.get("/api/v1/molecules/search", params={"q": "nước"})
    assert search.status_code == 200
    assert search.json()["results"][0]["id"] == "h2o"
    rules = client.get("/api/v1/rules/vsepr")
    assert len(rules.json()["rules"]) == 13
    explanation = client.post("/api/v1/explain", json={"molecule_id": "co2", "level": "basic"})
    assert explanation.status_code == 200
    assert explanation.json()["formula"] == "CO2"


def test_formula_input_length_limit() -> None:
    response = client.get("/api/v1/formula", params={"formula": "H" * 81})
    assert response.status_code == 422
