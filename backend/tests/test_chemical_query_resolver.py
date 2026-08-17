"""Unified query resolution: formulas, names, aliases, ambiguity and missing services."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi.testclient import TestClient
import pytest

from app.core.config import settings
from app.core.exceptions import AmbiguousMoleculeError, UnsupportedMoleculeError
from app.main import app
from app.schemas.analysis_schema import AnalysisRequest
from app.schemas.molecule_schema import ExternalServiceState, ExternalServiceStatus, PubChemCandidate
from app.services import chemical_query_resolver, molecule_resolver, pubchem_service
from app.services.analysis_service import analyze
from app.services.chemical_query_resolver import cas_for_identity, resolve_chemical_query
from app.services.connectivity_service import parse_molfile
from app.services.pubchem_service import PubChemLookupResult

client = TestClient(app)


def disabled_formula_lookup(_parsed) -> PubChemLookupResult:
    return PubChemLookupResult(candidates=[], status=ExternalServiceStatus(service="PubChem", state=ExternalServiceState.DISABLED))


def sulfate_candidate(cid: int = 1117) -> PubChemCandidate:
    return PubChemCandidate(
        id=f"pubchem:{cid}", cid=cid, formula="SO4^2-", charge=-2,
        name_vi="Sulfate", name_en="Sulfate", title="Sulfate",
        canonical_smiles="[O-]S(=O)(=O)[O-]", inchikey="QAOWNCQODCNURD-UHFFFAOYSA-L",
        covalent_unit_count=1, cache_timestamp=datetime.now(UTC),
    )


# --------------------------------------------------------------------------- #
# Formula queries
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("query", ["H2O", "SO4^2-", "NH4+", "NO3-", "ClF3", "CO3^2-"])
def test_a_valid_formula_is_resolved_as_a_formula(query: str) -> None:
    resolution = resolve_chemical_query(query)
    assert resolution.kind == "formula"
    assert resolution.parsed.formula == query


def test_a_formula_query_goes_through_the_deterministic_solver() -> None:
    """SO4^2- must reach the solver, not a name lookup."""

    result = analyze(AnalysisRequest(query="SO4^2-"))
    assert result.molecule.formula == "SO4^2-"
    assert result.vsepr.ax_en == "AX4"
    assert result.lewis.resonance_forms == 6
    assert result.lewis.total_valence_electrons == 32


def test_capitalisation_no_longer_decides_how_a_query_is_read() -> None:
    """The removed frontend heuristic treated any leading capital as a formula."""

    lower = resolve_chemical_query("water")
    upper = resolve_chemical_query("Water")
    assert lower.kind == upper.kind == "name"
    assert lower.parsed.formula == upper.parsed.formula == "H2O"
    # ...while a genuine formula is still read as one, whatever its case looks like.
    assert resolve_chemical_query("H2O").kind == "formula"


# --------------------------------------------------------------------------- #
# Name queries against local identities
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(("query", "formula"), [
    ("water", "H2O"), ("nước", "H2O"), ("nuoc", "H2O"),
    ("ammonia", "NH3"), ("amoniac", "NH3"),
    ("chlorine trifluoride", "ClF3"), ("ozone", "O3"),
    ("nitrate", "NO3-"), ("ammonium", "NH4+"), ("hydronium", "H3O+"),
])
def test_local_names_and_aliases_resolve_without_any_network(query: str, formula: str) -> None:
    resolution = resolve_chemical_query(query)
    assert resolution.kind == "name"
    assert resolution.parsed.formula == formula


def test_accents_and_case_are_normalized() -> None:
    assert resolve_chemical_query("  AMONIAC ").parsed.formula == "NH3"
    assert resolve_chemical_query("Sulfur Dioxide").parsed.formula == "SO2"


def test_a_name_query_runs_the_whole_pipeline() -> None:
    result = analyze(AnalysisRequest(query="chlorine trifluoride"))
    assert result.molecule.formula == "ClF3"
    assert result.vsepr.ax_en == "AX3E2"
    assert result.structure3d.is_experimental


def test_cas_lookup_serves_the_geometry_layer() -> None:
    assert cas_for_identity("ClF3", 0) == "7790-91-2"
    assert cas_for_identity("NH3", 0) == "7664-41-7"
    assert cas_for_identity("XeF7", 0) is None


# --------------------------------------------------------------------------- #
# External name resolution
# --------------------------------------------------------------------------- #


def test_a_name_absent_from_the_curated_json_resolves_externally(monkeypatch: pytest.MonkeyPatch) -> None:
    """`sulfate` is deliberately not in chemical_identities.json."""

    assert all("sulfate" not in name for identity in chemical_query_resolver.local_identities() for name in identity.names)
    monkeypatch.setattr(
        chemical_query_resolver, "lookup_pubchem_name",
        lambda _name: PubChemLookupResult(
            candidates=[sulfate_candidate()],
            status=ExternalServiceStatus(service="PubChem", state=ExternalServiceState.SUCCESS),
        ),
    )
    resolution = resolve_chemical_query("sulfate")
    assert resolution.kind == "name"
    assert resolution.parsed.formula == "SO4^2-"
    assert resolution.pubchem_cid == 1117


def test_an_externally_resolved_name_reaches_the_deterministic_solver(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        chemical_query_resolver, "lookup_pubchem_name",
        lambda _name: PubChemLookupResult(
            candidates=[sulfate_candidate()],
            status=ExternalServiceStatus(service="PubChem", state=ExternalServiceState.SUCCESS),
        ),
    )
    monkeypatch.setattr(molecule_resolver, "lookup_pubchem_formula", disabled_formula_lookup)
    result = analyze(AnalysisRequest(query="sulfate"))
    assert result.molecule.formula == "SO4^2-"
    assert result.vsepr.ax_en == "AX4"
    assert result.lewis.resonance_forms == 6


def test_several_distinct_candidates_are_returned_rather_than_silently_picking_the_first(monkeypatch: pytest.MonkeyPatch) -> None:
    first = sulfate_candidate(1117)
    second = sulfate_candidate(1118).model_copy(update={"inchikey": "DIFFERENT-KEY-L", "formula": "SO4^2-"})
    monkeypatch.setattr(
        chemical_query_resolver, "lookup_pubchem_name",
        lambda _name: PubChemLookupResult(
            candidates=[first, second],
            status=ExternalServiceStatus(service="PubChem", state=ExternalServiceState.AMBIGUOUS),
        ),
    )
    with pytest.raises(AmbiguousMoleculeError) as caught:
        resolve_chemical_query("sulfate")
    assert {item["cid"] for item in caught.value.candidates or []} == {1117, 1118}


def test_a_chosen_cid_disambiguates_without_retyping_the_query(monkeypatch: pytest.MonkeyPatch) -> None:
    first = sulfate_candidate(1117)
    second = sulfate_candidate(1118).model_copy(update={"inchikey": "DIFFERENT-KEY-L"})
    monkeypatch.setattr(
        chemical_query_resolver, "lookup_pubchem_name",
        lambda _name: PubChemLookupResult(
            candidates=[first, second],
            status=ExternalServiceStatus(service="PubChem", state=ExternalServiceState.AMBIGUOUS),
        ),
    )
    resolution = resolve_chemical_query("sulfate", pubchem_cid=1118)
    assert resolution.pubchem_cid == 1118


def test_missing_pubchem_yields_a_typed_refusal_not_a_guess(monkeypatch: pytest.MonkeyPatch) -> None:
    for state in (ExternalServiceState.DISABLED, ExternalServiceState.TIMEOUT, ExternalServiceState.NOT_FOUND):
        monkeypatch.setattr(
            chemical_query_resolver, "lookup_pubchem_name",
            lambda _name, state=state: PubChemLookupResult(
                candidates=[], status=ExternalServiceStatus(service="PubChem", state=state),
            ),
        )
        with pytest.raises(UnsupportedMoleculeError):
            resolve_chemical_query("some unheard-of substance")


def test_pubchem_name_lookup_validates_rows_before_accepting_them(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    """A salt or an out-of-scope element must not become a candidate."""

    import json

    payload = {"PropertyTable": {"Properties": [
        {"CID": 1, "MolecularFormula": "Na2SO4", "Charge": 0, "CovalentUnitCount": 3, "ConnectivitySMILES": "[Na+].[Na+].[O-]S(=O)(=O)[O-]"},
        {"CID": 2, "MolecularFormula": "FeCl3", "Charge": 0, "CovalentUnitCount": 1, "ConnectivitySMILES": "Cl[Fe](Cl)Cl"},
        {"CID": 3, "MolecularFormula": "O4S", "Charge": -2, "CovalentUnitCount": 1, "ConnectivitySMILES": "[O-]S(=O)(=O)[O-]"},
    ]}}
    monkeypatch.setattr(pubchem_service.settings, "ENABLE_PUBCHEM", True)
    monkeypatch.setattr(pubchem_service.settings, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(pubchem_service, "_request_bytes", lambda _url: (json.dumps(payload).encode(), ExternalServiceState.SUCCESS))
    result = pubchem_service.lookup_pubchem_name("sulfate")
    # The salt is rejected on covalent-unit count, the iron compound on element scope.
    assert [candidate.cid for candidate in result.candidates] == [3]
    assert result.candidates[0].formula == "SO4^2-"
    assert result.status.state is ExternalServiceState.SUCCESS


def test_name_lookup_results_are_cached(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    import json

    payload = {"PropertyTable": {"Properties": [
        {"CID": 3, "MolecularFormula": "O4S", "Charge": -2, "CovalentUnitCount": 1, "ConnectivitySMILES": "[O-]S(=O)(=O)[O-]"},
    ]}}
    calls: list[str] = []

    def request(url: str):
        calls.append(url)
        return json.dumps(payload).encode(), ExternalServiceState.SUCCESS

    monkeypatch.setattr(pubchem_service.settings, "ENABLE_PUBCHEM", True)
    monkeypatch.setattr(pubchem_service.settings, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(pubchem_service, "_request_bytes", request)
    pubchem_service.lookup_pubchem_name("sulfate")
    second = pubchem_service.lookup_pubchem_name("sulfate")
    assert len(calls) == 1
    assert second.status.state is ExternalServiceState.CACHE_HIT


def test_name_lookup_is_disabled_by_default() -> None:
    result = pubchem_service.lookup_pubchem_name("sulfate")
    assert result.candidates == []
    assert result.status.state is ExternalServiceState.DISABLED


# --------------------------------------------------------------------------- #
# API surface and search
# --------------------------------------------------------------------------- #


def test_analyze_accepts_a_raw_query_over_http() -> None:
    response = client.post("/api/v1/analyze", json={"query": "nước"})
    assert response.status_code == 200
    assert response.json()["molecule"]["formula"] == "H2O"


def test_analyze_requires_at_least_one_identity_field() -> None:
    assert client.post("/api/v1/analyze", json={}).status_code == 422


def test_search_looks_beyond_the_curated_records() -> None:
    """NF3 and ozone have identity entries but no curated molecule record."""

    curated_ids = {record["id"] for record in molecule_resolver.curated_records()}
    results = molecule_resolver.search_molecules("ozone")
    assert results
    assert results[0].formula == "O3"
    assert results[0].id not in curated_ids
    assert results[0].review_status == "identity_registry_pending_analysis"


def test_curated_search_results_still_win() -> None:
    results = molecule_resolver.search_molecules("nước")
    assert results[0].id == "h2o"


# --------------------------------------------------------------------------- #
# Connectivity abstraction
# --------------------------------------------------------------------------- #


def test_molfile_parser_reads_atoms_bonds_and_charges() -> None:
    molfile = """sulfate
  test

  5  4  0  0  0  0            999 V2000
    0.0000    0.0000    0.0000 S   0  0  0  0  0  0  0  0  0  0  0  0
    1.5000    0.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
   -0.5000    1.4000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
   -0.5000   -0.7000    1.2000 O   0  0  0  0  0  0  0  0  0  0  0  0
   -0.5000   -0.7000   -1.2000 O   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  2  0  0  0  0
  1  3  2  0  0  0  0
  1  4  1  0  0  0  0
  1  5  1  0  0  0  0
M  CHG  2   4  -1   5  -1
M  END
"""
    graph = parse_molfile(molfile)
    assert graph is not None
    assert dict(graph.inventory()) == {"S": 1, "O": 4}
    assert graph.total_charge == -2
    assert graph.fragment_count == 1
    assert graph.single_center_id("S") == "a0"
    assert graph.bond_order("a0", "a1") == 2
    assert graph.has_coordinates


def test_molfile_parser_detects_multiple_fragments() -> None:
    molfile = """salt
  test

  2  0  0  0  0  0            999 V2000
    0.0000    0.0000    0.0000 Na  0  0  0  0  0  0  0  0  0  0  0  0
    2.0000    0.0000    0.0000 Cl  0  0  0  0  0  0  0  0  0  0  0  0
M  END
"""
    graph = parse_molfile(molfile)
    assert graph is not None
    assert graph.fragment_count == 2
    assert graph.single_center_id() is None


def test_molfile_parser_rejects_garbage() -> None:
    assert parse_molfile("not a molfile") is None
    assert parse_molfile("  X  Y  0  0 V2000\nrubbish") is None


def test_the_custom_smiles_regex_parser_is_gone() -> None:
    """`_simple_smiles_graph` was a growing hand-written grammar; it must not return."""

    from app.services import deterministic_chemistry_service

    assert not hasattr(deterministic_chemistry_service, "_simple_smiles_graph")
    assert not hasattr(deterministic_chemistry_service, "_TERMINAL_SINGLE_BOND")


def test_smiles_connectivity_requires_a_real_parser(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services.connectivity_service import resolve_connectivity

    monkeypatch.setattr(settings, "ENABLE_RDKIT", False)
    result = resolve_connectivity(smiles="N(F)(F)F")
    assert result.graph is None
    assert result.status.state is ExternalServiceState.DISABLED
