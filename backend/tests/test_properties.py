"""Property normalization, provenance, applicability and lazy loading."""

from __future__ import annotations

import json
import time

from fastapi.testclient import TestClient
import pytest

from app.core.config import settings
from app.main import app
from app.properties.providers.base import (
    BULK_PHASE_PROPERTY_KEYS,
    PropertyQuery,
    applies_to_entity,
)
from app.properties.providers.computed import ComputedPropertyProvider, molar_mass
from app.properties.providers.pubchem_rest import PubChemRestPropertyProvider
from app.properties.providers.pubchem_view import PubChemViewPropertyProvider, discover_headings
from app.properties.schema import (
    NormalizedProperty,
    PropertyApplicability,
    PropertyCategory,
    PropertyEvidenceType,
)
from app.properties.service import fast_properties, full_properties
from app.schemas.analysis_schema import AnalysisRequest
from app.services import pubchem_service
from app.services.analysis_service import analyze
from app.services.molecule_resolver import get_record

client = TestClient(app)


def water_query() -> PropertyQuery:
    return PropertyQuery.from_record(get_record("h2o") | {"pubchem_cid": 962})


def nitrate_query() -> PropertyQuery:
    return PropertyQuery.from_record(get_record("no3-minus") | {"pubchem_cid": 943})


def view_payload(**sections: str) -> dict:
    return {"Record": {"Section": [
        {"TOCHeading": heading, "Information": [{"Value": {"StringWithMarkup": [{"String": text}]}}]}
        for heading, text in sections.items()
    ]}}


# --------------------------------------------------------------------------- #
# Normalized schema
# --------------------------------------------------------------------------- #


def test_a_missing_value_must_be_explained_not_left_blank() -> None:
    with pytest.raises(ValueError, match="not_applicable or unavailable"):
        NormalizedProperty(
            key="melting_point", category=PropertyCategory.PHYSICAL,
            label_vi="a", label_en="b", value=None,
            evidence_type=PropertyEvidenceType.EXPERIMENTAL, source_name="test",
        )


def test_a_present_value_cannot_be_marked_missing() -> None:
    with pytest.raises(ValueError, match="cannot be marked"):
        NormalizedProperty(
            key="melting_point", category=PropertyCategory.PHYSICAL,
            label_vi="a", label_en="b", value="0 °C",
            evidence_type=PropertyEvidenceType.EXPERIMENTAL, source_name="test",
            applicability=PropertyApplicability.NOT_APPLICABLE,
        )


def test_every_property_carries_bilingual_labels_and_a_source() -> None:
    for item in fast_properties(water_query()).properties:
        assert item.label_vi and item.label_en
        assert item.source_name
        assert item.category in set(PropertyCategory)
        assert item.evidence_type in set(PropertyEvidenceType)


# --------------------------------------------------------------------------- #
# Computed provider
# --------------------------------------------------------------------------- #


def test_molar_mass_is_computed_from_standard_atomic_weights() -> None:
    assert molar_mass({"H": 2, "O": 1}) == pytest.approx(18.015, abs=0.001)
    assert molar_mass({"S": 1, "O": 4}) == pytest.approx(96.056, abs=0.01)
    assert molar_mass({"Fe": 1}) is None


def test_computed_provider_needs_no_network() -> None:
    result = ComputedPropertyProvider().fetch(water_query())
    keys = {item.key for item in result.properties}
    assert {"molar_mass", "central_atom_electronegativity", "polarity"} <= keys
    assert result.status is not None and result.status.state == "success"


def test_polarity_is_curated_or_explicitly_unavailable() -> None:
    curated = {item.key: item for item in fast_properties(water_query()).properties}
    assert curated["polarity"].evidence_type is PropertyEvidenceType.CURATED
    assert curated["polarity"].value

    from app.services.formula_parser import parse_formula
    from app.services.deterministic_chemistry_service import build_deterministic_record

    uncurated = build_deterministic_record(parse_formula("H2S"))
    item = {row.key: row for row in fast_properties(PropertyQuery.from_record(uncurated)).properties}["polarity"]
    assert item.applicability is PropertyApplicability.UNAVAILABLE
    assert item.value is None
    assert item.notes_en


# --------------------------------------------------------------------------- #
# Ion applicability
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("key", sorted(BULK_PHASE_PROPERTY_KEYS))
def test_bulk_properties_do_not_apply_to_an_isolated_ion(key: str) -> None:
    assert applies_to_entity(key, water_query()) is True
    assert applies_to_entity(key, nitrate_query()) is False
    assert applies_to_entity(key, nitrate_query(), source_describes_exact_entity=True) is True


def test_structural_properties_still_apply_to_an_ion() -> None:
    assert applies_to_entity("ax_en", nitrate_query()) is True
    assert applies_to_entity("molar_mass", nitrate_query()) is True


def test_an_ions_melting_point_is_reported_as_not_applicable_not_borrowed(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """A melting point on a nitrate record belongs to a nitrate salt, not to NO3-."""

    monkeypatch.setattr(settings, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(settings, "ENABLE_PUBCHEM", True)
    monkeypatch.setattr(settings, "ENABLE_PUBCHEM_PROPERTIES", True)
    payload = view_payload(**{
        "Melting Point": "308 °C",
        "Boiling Point": "380 °C",
        "Physical Description": "White crystalline solid",
    })
    monkeypatch.setattr(pubchem_service, "_request_bytes", lambda _url: (json.dumps(payload).encode(), "success"))
    monkeypatch.setattr(
        "app.properties.providers.pubchem_view._request_bytes",
        lambda _url: (json.dumps(payload).encode(), _SuccessState()),
    )
    properties = {item.key: item for item in PubChemViewPropertyProvider().fetch(nitrate_query()).properties}
    assert properties["melting_point"].applicability is PropertyApplicability.NOT_APPLICABLE
    assert properties["melting_point"].value is None
    assert "salt" in (properties["melting_point"].notes_en or "")
    assert properties["boiling_point"].applicability is PropertyApplicability.NOT_APPLICABLE
    # A non-bulk annotation is still reported.
    assert properties["physical_description"].value == "White crystalline solid"


class _SuccessState:
    value = "success"


def test_a_neutral_molecule_keeps_its_measured_bulk_properties(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(settings, "ENABLE_PUBCHEM", True)
    monkeypatch.setattr(settings, "ENABLE_PUBCHEM_PROPERTIES", True)
    payload = view_payload(**{"Melting Point": "0 °C", "Boiling Point": "100 °C"})
    monkeypatch.setattr(
        "app.properties.providers.pubchem_view._request_bytes",
        lambda _url: (json.dumps(payload).encode(), _SuccessState()),
    )
    properties = {item.key: item for item in PubChemViewPropertyProvider().fetch(water_query()).properties}
    assert properties["melting_point"].value == "0 °C"
    assert properties["melting_point"].evidence_type is PropertyEvidenceType.EXPERIMENTAL
    assert properties["melting_point"].applicability is PropertyApplicability.APPLICABLE
    assert properties["melting_point"].source_name == "PubChem"
    assert properties["melting_point"].source_url


# --------------------------------------------------------------------------- #
# Heading discovery
# --------------------------------------------------------------------------- #


def test_headings_are_discovered_not_assumed() -> None:
    payload = view_payload(**{"Melting Point": "0 °C", "Odor": "Odourless"})
    headings = discover_headings(payload)
    assert set(headings) == {"Melting Point", "Odor"}


def test_absent_headings_simply_produce_no_row(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """Missing data must remain missing; nothing is invented to fill the table."""

    monkeypatch.setattr(settings, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(settings, "ENABLE_PUBCHEM", True)
    monkeypatch.setattr(settings, "ENABLE_PUBCHEM_PROPERTIES", True)
    payload = view_payload(**{"Odor": "Odourless"})
    monkeypatch.setattr(
        "app.properties.providers.pubchem_view._request_bytes",
        lambda _url: (json.dumps(payload).encode(), _SuccessState()),
    )
    keys = {item.key for item in PubChemViewPropertyProvider().fetch(water_query()).properties}
    assert keys == {"odor"}
    assert "melting_point" not in keys


# --------------------------------------------------------------------------- #
# External behaviour: disabled, cached, failing
# --------------------------------------------------------------------------- #


def test_external_property_providers_are_disabled_by_default() -> None:
    for provider in (PubChemRestPropertyProvider(), PubChemViewPropertyProvider()):
        result = provider.fetch(water_query())
        assert result.properties == ()
        assert result.status is not None and result.status.state == "disabled"


def test_rest_provider_caches_its_payload(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setattr(settings, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(settings, "ENABLE_PUBCHEM", True)
    monkeypatch.setattr(settings, "ENABLE_PUBCHEM_PROPERTIES", True)
    payload = {"PropertyTable": {"Properties": [{"ExactMass": "18.010565", "XLogP": -0.5, "TPSA": 1.0}]}}
    calls: list[str] = []

    def request(url: str, **kwargs):
        calls.append(url)
        return json.dumps(payload).encode(), _SuccessState()

    monkeypatch.setattr("app.properties.providers.pubchem_rest._request_bytes", request)
    first = PubChemRestPropertyProvider().fetch(water_query())
    second = PubChemRestPropertyProvider().fetch(water_query())
    assert len(calls) == 1
    assert second.status is not None and second.status.cache_hit is True
    keys = {item.key for item in first.properties}
    assert {"pubchem_cid", "exact_mass", "xlogp", "tpsa"} <= keys
    assert any(item.evidence_type is PropertyEvidenceType.COMPUTED for item in first.properties)


def test_a_failing_provider_never_empties_the_table(monkeypatch: pytest.MonkeyPatch) -> None:
    class Exploding:
        name = "exploding"
        service = "PubChem"

        def fetch(self, _query):
            raise RuntimeError("boom")

    monkeypatch.setattr(
        "app.properties.service._PROVIDER_ORDER",
        (ComputedPropertyProvider, Exploding),
    )
    bundle = full_properties(water_query())
    assert bundle.partial is True
    assert any(status.state == "temporary_failure" for status in bundle.statuses)
    assert {item.key for item in bundle.properties} >= {"molar_mass"}


def test_the_property_budget_skips_external_providers_but_keeps_local_ones() -> None:
    bundle = full_properties(water_query(), budget_seconds=-1.0)
    assert {item.key for item in bundle.properties} >= {"molar_mass"}
    assert bundle.partial is True
    assert any(status.state == "timeout" for status in bundle.statuses)


def test_earlier_providers_win_on_a_duplicate_key(monkeypatch: pytest.MonkeyPatch) -> None:
    class Overwriter:
        name = "overwriter"
        service = "PubChem"

        def fetch(self, _query):
            from app.properties.providers.base import PropertyProviderResult
            from app.properties.schema import PropertyProviderStatus

            return PropertyProviderResult(
                (NormalizedProperty(
                    key="molar_mass", category=PropertyCategory.PHYSICAL,
                    label_vi="x", label_en="x", value=999.0,
                    evidence_type=PropertyEvidenceType.COMPUTED, source_name="bogus",
                ),),
                PropertyProviderStatus(provider="overwriter", service="PubChem", state="success"),
            )

    monkeypatch.setattr("app.properties.service._PROVIDER_ORDER", (ComputedPropertyProvider, Overwriter))
    bundle = full_properties(water_query())
    mass = next(item for item in bundle.properties if item.key == "molar_mass")
    assert mass.value == pytest.approx(18.015, abs=0.001)


# --------------------------------------------------------------------------- #
# Wiring: fast inline vs lazy endpoint
# --------------------------------------------------------------------------- #


def test_analyze_returns_only_local_properties_and_makes_no_property_call(monkeypatch: pytest.MonkeyPatch) -> None:
    """/analyze must stay responsive: no property provider may touch the network there."""

    def explode(_url: str):
        raise AssertionError("/analyze must not perform property requests")

    monkeypatch.setattr("app.properties.providers.pubchem_rest._request_bytes", explode)
    monkeypatch.setattr("app.properties.providers.pubchem_view._request_bytes", explode)
    result = analyze(AnalysisRequest(molecule_id="h2o"))
    assert result.properties
    # The curated local property snapshot (app/data/curated_properties.json) legitimately
    # carries EXPERIMENTAL/SOURCE_ANNOTATION evidence types -- those describe how the fact
    # was originally measured, not whether fetching it touched the network just now. The
    # actual network-safety guarantee is the monkeypatched _request_bytes above never firing.
    assert all(
        item.evidence_type in {
            PropertyEvidenceType.DETERMINISTIC, PropertyEvidenceType.COMPUTED,
            PropertyEvidenceType.CURATED, PropertyEvidenceType.EXPERIMENTAL,
            PropertyEvidenceType.SOURCE_ANNOTATION,
        }
        for item in result.properties
    )


def test_analyze_stays_fast() -> None:
    started = time.perf_counter()
    analyze(AnalysisRequest(molecule_id="clf3"))
    assert time.perf_counter() - started < 1.0


def test_the_lazy_endpoint_returns_a_bundle_with_statuses() -> None:
    response = client.post("/api/v1/properties", json={"molecule_id": "h2o"})
    assert response.status_code == 200
    body = response.json()
    assert body["schema_version"] == "2.0"
    assert body["formula"] == "H2O"
    assert body["properties"]
    assert body["statuses"]


def test_the_lazy_endpoint_accepts_a_formula() -> None:
    response = client.post("/api/v1/properties", json={"formula": "NO3-"})
    assert response.status_code == 200
    assert response.json()["charge"] == -1


def test_the_lazy_endpoint_requires_an_identity() -> None:
    assert client.post("/api/v1/properties", json={}).status_code == 422


def test_no_llm_is_involved_in_property_values() -> None:
    """Property values must never come from the explanation layer."""

    from pathlib import Path

    for name in ("schema.py", "service.py"):
        source = (Path(__file__).resolve().parents[1] / "app" / "properties" / name).read_text()
        assert "llm" not in source.casefold()
        assert "openrouter" not in source.casefold()
