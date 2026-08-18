"""Molecule Data admin CRUD/validate/preview/revert, and the 401 boundary.

Every test gets its own throwaway DATA_DIR (a pytest tmp_path), so the real
catalog under backend/app/data is never touched, and the four baseline
@lru_cache loaders the admin service can invalidate are cleared before and
after each test so no state leaks between tests that reuse the same process.
"""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services import molecule_admin_service

ADMIN_ROUTES = [
    ("get", "/api/v1/admin/molecules"),
    ("get", "/api/v1/admin/molecules/nh3"),
    ("post", "/api/v1/admin/molecules"),
    ("put", "/api/v1/admin/molecules/nh3"),
    ("post", "/api/v1/admin/molecules/nh3/validate"),
    ("post", "/api/v1/admin/molecules/preview"),
    ("post", "/api/v1/admin/molecules/nh3/revert"),
    ("get", "/api/v1/admin/molecules/nh3/completeness"),
    ("get", "/api/v1/admin/molecules/export"),
]


@pytest.fixture(autouse=True)
def _isolated_data_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATA_DIR", tmp_path)
    molecule_admin_service.reload_effective_catalog()
    yield
    molecule_admin_service.reload_effective_catalog()


@pytest.fixture
def admin_client() -> TestClient:
    session_client = TestClient(app)
    login = session_client.post("/api/v1/admin/login", json={"username": "admin", "password": "admin@123"})
    assert login.status_code == 200
    return session_client


def test_every_admin_route_401s_without_a_session() -> None:
    anon = TestClient(app)
    for method, path in ADMIN_ROUTES:
        kwargs = {"json": {}} if method in ("post", "put") else {}
        response = getattr(anon, method)(path, **kwargs)
        assert response.status_code == 401, f"{method.upper()} {path} should 401 without a session"


def test_authenticated_list_and_read(admin_client: TestClient) -> None:
    listed = admin_client.get("/api/v1/admin/molecules", params={"q": "NH3"})
    assert listed.status_code == 200
    ids = [item["id"] for item in listed.json()["results"]]
    assert "nh3" in ids

    fetched = admin_client.get("/api/v1/admin/molecules/nh3")
    assert fetched.status_code == 200
    body = fetched.json()
    assert body["molecule"]["formula"] == "NH3"
    assert body["has_override"] is False
    assert len(body["properties"]) > 0


def test_unknown_molecule_is_404(admin_client: TestClient) -> None:
    response = admin_client.get("/api/v1/admin/molecules/not-a-real-molecule")
    assert response.status_code == 404


def test_validate_reports_errors_for_inconsistent_data(admin_client: TestClient) -> None:
    draft = admin_client.get("/api/v1/admin/molecules/nh3").json()["molecule"]
    draft["steric_number"] = 99  # bonding_domains + lone_pair_domains != 99
    response = admin_client.post(
        "/api/v1/admin/molecules/nh3/validate", json={"molecule": draft, "properties": []}
    )
    assert response.status_code == 200
    report = response.json()
    assert report["is_valid"] is False
    assert any(issue["field"] == "steric_number" for issue in report["errors"])


def test_validate_flags_duplicate_formula_and_charge(admin_client: TestClient) -> None:
    nh3 = admin_client.get("/api/v1/admin/molecules/nh3").json()["molecule"]
    duplicate = dict(nh3)
    duplicate["id"] = "nh3-duplicate"
    response = admin_client.post(
        "/api/v1/admin/molecules/nh3-duplicate/validate", json={"molecule": duplicate, "properties": []}
    )
    report = response.json()
    assert report["is_valid"] is False
    assert any(issue["field"] == "formula" for issue in report["errors"])


def test_save_is_blocked_by_validation_errors(admin_client: TestClient) -> None:
    draft = admin_client.get("/api/v1/admin/molecules/nh3").json()["molecule"]
    draft["bond_orders"] = [1, 1]  # wrong length: should be len(atom_symbols) - 1 == 3
    response = admin_client.put("/api/v1/admin/molecules/nh3", json={"molecule": draft, "properties": []})
    assert response.status_code == 422
    assert response.json()["detail"]["is_valid"] is False


def test_preview_uses_the_real_chemistry_pipeline(admin_client: TestClient) -> None:
    draft = admin_client.get("/api/v1/admin/molecules/nh3").json()["molecule"]
    response = admin_client.post("/api/v1/admin/molecules/preview", json={"molecule": draft, "properties": []})
    assert response.status_code == 200
    body = response.json()
    assert body["vsepr"]["ax_en"] == "AX3E"
    assert body["lewis"]["total_valence_electrons"] == 8
    assert body["structure3d"]["atoms"]


def test_save_persists_and_analyze_reflects_it_immediately(admin_client: TestClient, tmp_path) -> None:
    draft = admin_client.get("/api/v1/admin/molecules/nh3").json()["molecule"]
    draft["teaching_note_vi"] = "EDITED_NOTE_FOR_TEST"

    saved = admin_client.put("/api/v1/admin/molecules/nh3", json={"molecule": draft, "properties": []})
    assert saved.status_code == 200
    assert saved.json()["validation"]["is_valid"] is True

    override_file = tmp_path / "molecule_catalog_overrides.json"
    assert override_file.exists()
    on_disk = json.loads(override_file.read_text())
    assert any(item["id"] == "nh3" for item in on_disk["molecules"])

    # No restart needed: /analyze reads through the same cache the admin service cleared.
    analyzed = TestClient(app).post("/api/v1/analyze", json={"formula": "NH3"})
    assert analyzed.status_code == 200
    assert analyzed.json()["vsepr"]["teaching_note_vi"] == "EDITED_NOTE_FOR_TEST"


def test_revert_restores_baseline_and_reload_needs_no_restart(admin_client: TestClient) -> None:
    draft = admin_client.get("/api/v1/admin/molecules/nh3").json()["molecule"]
    draft["teaching_note_vi"] = "TEMPORARY_EDIT"
    admin_client.put("/api/v1/admin/molecules/nh3", json={"molecule": draft, "properties": []})

    reverted = admin_client.post("/api/v1/admin/molecules/nh3/revert")
    assert reverted.status_code == 200
    assert reverted.json() == {"had_override": True, "reverted_to_baseline": True}

    analyzed = TestClient(app).post("/api/v1/analyze", json={"formula": "NH3"})
    assert analyzed.json()["vsepr"]["teaching_note_vi"] != "TEMPORARY_EDIT"


def test_add_new_molecule_via_deterministic_draft_then_save(admin_client: TestClient) -> None:
    draft_response = admin_client.post(
        "/api/v1/admin/molecules/draft", json={"formula": "PH3", "charge": 0, "id": "ph3-test"}
    )
    assert draft_response.status_code == 200
    draft = draft_response.json()
    assert draft["source"] == "deterministic"

    created = admin_client.post("/api/v1/admin/molecules", json={"molecule": draft, "properties": []})
    assert created.status_code == 200
    assert created.json()["molecule"]["is_admin_added"] is True

    listed = admin_client.get("/api/v1/admin/molecules", params={"q": "PH3"})
    assert any(item["id"] == "ph3-test" for item in listed.json()["results"])


def test_experimental_geometry_round_trips_and_revert_restores_baseline(admin_client: TestClient) -> None:
    nh3 = admin_client.get("/api/v1/admin/molecules/nh3").json()["molecule"]
    geometry = {
        "id": "placeholder",
        "identity": {"formula": "NH3", "charge": 0, "atom_inventory": {"N": 1, "H": 3}},
        "evidence_type": "experimental",
        "atoms": [
            {"id": "a0", "element": "N", "role": "center"},
            {"id": "a1", "element": "H", "role": "ligand"},
            {"id": "a2", "element": "H", "role": "ligand"},
            {"id": "a3", "element": "H", "role": "ligand"},
        ],
        "bonds": [
            {"atom1_id": "a0", "atom2_id": "a1", "order": 1},
            {"atom1_id": "a0", "atom2_id": "a2", "order": 1},
            {"atom1_id": "a0", "atom2_id": "a3", "order": 1},
        ],
        "bond_lengths": [],
        "bond_angles": [
            {"id": "test-a1", "atom1_id": "a1", "center_atom_id": "a0", "atom2_id": "a2", "value_deg": 106.7, "equivalent_count": 3, "label": "H-N-H"},
        ],
        "dihedrals": [],
        "source": {"name": "Test-only source", "reference": "unit-test"},
    }
    saved = admin_client.put(
        "/api/v1/admin/molecules/nh3", json={"molecule": nh3, "experimental_geometry": geometry, "properties": []}
    )
    assert saved.status_code == 200

    fetched = admin_client.get("/api/v1/admin/molecules/nh3").json()
    assert fetched["experimental_geometry"] is not None
    assert fetched["experimental_geometry"]["source"]["name"] == "Test-only source"

    analyzed = TestClient(app).post("/api/v1/analyze", json={"formula": "NH3"})
    assert analyzed.json()["structure3d"]["is_experimental"] is True

    admin_client.post("/api/v1/admin/molecules/nh3/revert")
    reverted = admin_client.get("/api/v1/admin/molecules/nh3").json()
    assert reverted["experimental_geometry"]["source"]["name"] == "NIST CCCBDB"


def test_properties_round_trip_and_revert(admin_client: TestClient) -> None:
    nh3 = admin_client.get("/api/v1/admin/molecules/nh3").json()["molecule"]
    properties = [
        {
            "key": "molar_mass", "category": "physical", "label_vi": "Khối lượng mol", "label_en": "Molar mass",
            "value": 17.03, "unit": "g/mol", "evidence_type": "curated", "source_name": "unit-test",
        }
    ]
    saved = admin_client.put(
        "/api/v1/admin/molecules/nh3", json={"molecule": nh3, "properties": properties}
    )
    assert saved.status_code == 200

    fetched = admin_client.get("/api/v1/admin/molecules/nh3").json()
    assert [p["key"] for p in fetched["properties"]] == ["molar_mass"]

    admin_client.post("/api/v1/admin/molecules/nh3/revert")
    reverted = admin_client.get("/api/v1/admin/molecules/nh3").json()
    assert [p["key"] for p in reverted["properties"]] != ["molar_mass"]


def test_completeness_report(admin_client: TestClient) -> None:
    response = admin_client.get("/api/v1/admin/molecules/nh3/completeness")
    assert response.status_code == 200
    body = response.json()
    assert body["molecule_id"] == "nh3"
    assert 0 <= body["completeness_percent"] <= 100
