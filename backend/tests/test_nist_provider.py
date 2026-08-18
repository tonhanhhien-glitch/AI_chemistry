"""NIST CCCBDB adapter and provider: parsing, normalization, caching and failure modes.

Every test runs against saved HTML fixtures or monkeypatched transport. Nothing here
touches the network.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.config import settings
from app.geometry.adapters import nist_cccbdb_adapter as adapter
from app.geometry.fitter import angle_degrees, distance, fit_cartesian_coordinates
from app.geometry.providers import nist_cccbdb
from app.geometry.providers.base import GeometryQuery
from app.geometry.providers.nist_cccbdb import NistCccbdbProvider
from app.schemas.geometry_evidence_schema import GeometryEvidenceType, GeometryIdentity
from app.schemas.molecule_schema import ExternalServiceState

FIXTURES = Path(__file__).parent / "fixtures"


def clf3_identity() -> GeometryIdentity:
    return GeometryIdentity(
        formula="ClF3", charge=0, atom_inventory={"Cl": 1, "F": 3}, cas_rn="7790-91-2",
    )


def clf3_html() -> str:
    return (FIXTURES / "cccbdb_clf3_experimental.html").read_text(encoding="utf-8")


def sif4_html() -> str:
    return (FIXTURES / "cccbdb_sif4_experimental.html").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- #
# Parser / normalizer
# --------------------------------------------------------------------------- #


def test_parser_normalizes_a_full_cccbdb_geometry_page() -> None:
    evidence = adapter.parse_cccbdb_geometry_html(
        clf3_html(), identity=clf3_identity(), source_url="https://example.invalid/clf3",
        reference="2001Muller",
    )
    assert evidence is not None
    assert evidence.evidence_type is GeometryEvidenceType.EXPERIMENTAL
    assert evidence.point_group == "C2v"
    assert evidence.electronic_state == "X 1A1"
    assert evidence.phase == "gas"
    assert evidence.source.name == "NIST CCCBDB"
    assert evidence.source.reference == "2001Muller"
    assert evidence.source.retrieved_at is not None

    # The centre is derived from the angle rows, not from any per-molecule knowledge.
    center = evidence.center_atom_id
    assert center is not None
    assert evidence.atom_elements()[center] == "Cl"
    assert sorted(atom.element for atom in evidence.atoms) == ["Cl", "F", "F", "F"]
    assert len(evidence.bonds) == 3

    assert sorted(item.value_angstrom for item in evidence.bond_lengths) == [1.598, 1.698, 1.698]
    assert sorted(item.value_deg for item in evidence.bond_angles) == [87.45, 87.45, 174.9]


def test_parsed_page_fits_coordinates_that_reproduce_its_own_numbers() -> None:
    evidence = adapter.parse_cccbdb_geometry_html(
        clf3_html(), identity=clf3_identity(), source_url="https://example.invalid/clf3",
    )
    assert evidence is not None
    result = fit_cartesian_coordinates(evidence)
    assert result.accepted and result.coordinates is not None
    points = {item.id: (item.x, item.y, item.z) for item in result.coordinates}
    center = evidence.center_atom_id
    assert center is not None
    ligands = [atom.id for atom in evidence.atoms if atom.id != center]
    angles = sorted(
        round(angle_degrees(points[first], points[center], points[second]), 2)
        for index, first in enumerate(ligands) for second in ligands[index + 1:]
    )
    assert angles == [87.45, 87.45, 174.9]
    assert sorted(round(distance(points[center], points[ligand]), 3) for ligand in ligands) == [1.598, 1.698, 1.698]


def test_parser_maps_real_cccbdb_numeric_indices_to_cartesian_labels() -> None:
    """Real CCCBDB pages have internal coordinates (1 2, 2 1 3) and Cartesian rows (Cl1, F2, F3, F4)."""
    real_table_html = """
    <html><body>
    <h1>Experimental data for ClF3</h1>
    <p>Point group C2v</p>
    <h2>Internal coordinates</h2>
    <table>
      <tr><th>Descriptor</th><th>Value</th><th>Definition</th></tr>
      <tr><td>rFCl</td><td>1.597</td><td>1 2</td></tr>
      <tr><td>rFCl</td><td>1.697</td><td>1 3</td></tr>
      <tr><td>aFClF</td><td>87.45</td><td>2 1 3</td></tr>
      <tr><td>aFClF</td><td>174.9</td><td>3 1 4</td></tr>
    </table>
    <h2>Cartesian coordinates</h2>
    <table>
      <tr><th>Atom</th><th>X</th><th>Y</th><th>Z</th></tr>
      <tr><td>Cl1</td><td>0.0000</td><td>0.0000</td><td>0.0000</td></tr>
      <tr><td>F2</td><td>1.5970</td><td>0.0000</td><td>0.0000</td></tr>
      <tr><td>F3</td><td>0.0755</td><td>1.6953</td><td>0.0000</td></tr>
      <tr><td>F4</td><td>0.0755</td><td>-1.6953</td><td>0.0000</td></tr>
    </table>
    </body></html>
    """
    evidence = adapter.parse_cccbdb_geometry_html(
        real_table_html, identity=clf3_identity(), source_url="https://example.invalid/clf3",
    )
    assert evidence is not None
    assert evidence.coordinates is not None
    assert len(evidence.coordinates) == 4
    # Directly validated against reported constraints without fitting
    fit = fit_cartesian_coordinates(evidence)
    assert fit.accepted and fit.coordinates is not None
    assert not fit.coordinates_are_fitted


def test_parser_reads_dihedral_tables() -> None:
    html = (FIXTURES / "cccbdb_h2o2_dihedral.html").read_text(encoding="utf-8")
    evidence = adapter.parse_cccbdb_geometry_html(
        html, identity=GeometryIdentity(formula="H2O2", charge=0, atom_inventory={"H": 2, "O": 2}),
        source_url="https://example.invalid/h2o2",
    )
    assert evidence is not None
    assert len(evidence.dihedrals) == 1
    assert evidence.dihedrals[0].value_deg == 111.5
    assert len(evidence.bond_lengths) == 3
    assert len(evidence.bond_angles) == 2


def test_parser_returns_none_for_a_page_with_no_geometry() -> None:
    html = (FIXTURES / "cccbdb_no_geometry.html").read_text(encoding="utf-8")
    assert adapter.parse_cccbdb_geometry_html(
        html, identity=clf3_identity(), source_url="https://example.invalid/none",
    ) is None


def test_parser_rejects_a_page_whose_atoms_contradict_the_requested_inventory() -> None:
    """A wrong page must produce nothing rather than a half-populated record."""

    wrong = GeometryIdentity(formula="NF3", charge=0, atom_inventory={"N": 1, "F": 3})
    assert adapter.parse_cccbdb_geometry_html(
        clf3_html(), identity=wrong, source_url="https://example.invalid/clf3",
    ) is None


def test_parser_survives_malformed_html() -> None:
    assert adapter.parse_cccbdb_geometry_html(
        "<html><table><tr><td>Bond Lengths<td>oops", identity=clf3_identity(),
        source_url="https://example.invalid/broken",
    ) is None


def test_cccbdb_url_uses_the_digits_of_the_cas_number() -> None:
    assert adapter.cccbdb_url("7790-91-2").endswith("expgeom2x.asp?casno=7790912&charge=0")
    assert adapter.cccbdb_url("7790-91-2", charge=1).endswith("expgeom2x.asp?casno=7790912&charge=1")


def test_dynamic_cas_resolution_from_pubchem_synonyms(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """An arbitrary new molecule with a PubChem CID resolves CAS from synonyms and queries NIST."""
    from app.services import pubchem_service
    monkeypatch.setattr(settings, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(settings, "ENABLE_NIST_CCCBDB", True)
    monkeypatch.setattr(settings, "ENABLE_PUBCHEM", True)

    monkeypatch.setattr(pubchem_service, "fetch_pubchem_cas_rn", lambda cid, **kwargs: "7783-61-1" if cid == 24556 else None)
    monkeypatch.setattr(nist_cccbdb, "fetch_cccbdb_geometry_html", lambda cas, **kwargs: (sif4_html(), ExternalServiceState.SUCCESS))

    query = GeometryQuery(formula="SiF4", charge=0, atom_inventory={"Si": 1, "F": 4}, pubchem_cid=24556)
    result = NistCccbdbProvider().fetch(query)
    assert result.evidence is not None
    assert result.status.state is ExternalServiceState.SUCCESS


# --------------------------------------------------------------------------- #
# Provider: snapshot, cache, live fetch, failure
# --------------------------------------------------------------------------- #


def test_provider_serves_the_local_snapshot_without_touching_the_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def explode(_cas: str):
        raise AssertionError("the snapshot must be consulted before any fetch")

    monkeypatch.setattr(nist_cccbdb, "fetch_cccbdb_geometry_html", explode)
    result = NistCccbdbProvider().fetch(GeometryQuery(formula="ClF3", charge=0, atom_inventory={"Cl": 1, "F": 3}))
    assert result.evidence is not None
    assert result.status.cache_hit is True
    assert result.status.service == "Local geometry snapshot"


def test_provider_is_disabled_by_default_and_reports_it(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(settings, "ENABLE_NIST_CCCBDB", False)
    result = NistCccbdbProvider().fetch(GeometryQuery(formula="SiF4", charge=0, atom_inventory={"Si": 1, "F": 4}, cas_rn="7783-61-1"))
    assert result.evidence is None
    assert result.status.state is ExternalServiceState.DISABLED


def test_live_fetch_normalizes_and_caches_so_no_source_edit_is_needed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """A newly discovered species must persist without anyone editing a JSON file."""

    monkeypatch.setattr(settings, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(settings, "ENABLE_NIST_CCCBDB", True)
    calls: list[str] = []

    def fetch(cas: str, **kwargs):
        calls.append(cas)
        return sif4_html(), ExternalServiceState.SUCCESS

    monkeypatch.setattr(nist_cccbdb, "fetch_cccbdb_geometry_html", fetch)
    # SiF4 is absent from the shipped snapshot: exactly the "newly supported molecule"
    # case that used to require a source-code edit.
    query = GeometryQuery(
        formula="SiF4", charge=0, atom_inventory={"Si": 1, "F": 4}, cas_rn="7783-61-1",
    )
    first = NistCccbdbProvider().fetch(query)
    assert first.evidence is not None
    assert first.status.state is ExternalServiceState.SUCCESS
    assert calls == ["7783-61-1"]

    cache_file = tmp_path / "nist_geometry_cache.json"
    assert cache_file.exists()
    stored = json.loads(cache_file.read_text())
    assert any("evidence" in entry for entry in stored.values())

    second = NistCccbdbProvider().fetch(query)
    assert second.evidence is not None
    assert second.status.state is ExternalServiceState.CACHE_HIT
    assert second.status.cache_hit is True
    assert calls == ["7783-61-1"], "the second lookup must be served from the cache"


@pytest.mark.parametrize("state", [
    ExternalServiceState.TIMEOUT,
    ExternalServiceState.TEMPORARY_FAILURE,
    ExternalServiceState.RATE_LIMITED,
    ExternalServiceState.NOT_FOUND,
])
def test_transport_failures_are_typed_and_never_raise(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, state: ExternalServiceState) -> None:
    monkeypatch.setattr(settings, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(settings, "ENABLE_NIST_CCCBDB", True)
    monkeypatch.setattr(nist_cccbdb, "fetch_cccbdb_geometry_html", lambda _cas, **kwargs: (None, state))
    result = NistCccbdbProvider().fetch(GeometryQuery(
        formula="SiF4", charge=0, atom_inventory={"Si": 1, "F": 4}, cas_rn="7783-61-1",
    ))
    assert result.evidence is None
    assert result.status.state is state


def test_unparseable_live_page_is_reported_not_stored(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(settings, "ENABLE_NIST_CCCBDB", True)
    monkeypatch.setattr(nist_cccbdb, "fetch_cccbdb_geometry_html", lambda _cas, **kwargs: ("<html>nothing</html>", ExternalServiceState.SUCCESS))
    result = NistCccbdbProvider().fetch(GeometryQuery(
        formula="SiF4", charge=0, atom_inventory={"Si": 1, "F": 4}, cas_rn="7783-61-1",
    ))
    assert result.evidence is None
    assert result.status.state is ExternalServiceState.INVALID_RESPONSE
    assert not (tmp_path / "nist_geometry_cache.json").exists()


def test_missing_cas_is_a_typed_miss_not_an_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(settings, "ENABLE_NIST_CCCBDB", True)
    result = NistCccbdbProvider().fetch(GeometryQuery(formula="SiF4", charge=0, atom_inventory={"Si": 1, "F": 4}))
    assert result.evidence is None
    assert result.status.state is ExternalServiceState.NOT_FOUND


def test_expired_cache_entries_are_ignored(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(settings, "ENABLE_NIST_CCCBDB", True)
    monkeypatch.setattr(settings, "NIST_CACHE_TTL_SECONDS", 0)
    monkeypatch.setattr(nist_cccbdb, "fetch_cccbdb_geometry_html", lambda _cas, **kwargs: (sif4_html(), ExternalServiceState.SUCCESS))
    query = GeometryQuery(
        formula="SiF4", charge=0, atom_inventory={"Si": 1, "F": 4}, cas_rn="7783-61-1",
    )
    NistCccbdbProvider().fetch(query)
    second = NistCccbdbProvider().fetch(query)
    assert second.status.state is ExternalServiceState.SUCCESS, "an expired entry must be refetched"


def test_ambiguous_snapshot_matches_are_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """Two records matching one identity means the identity is not pinned; answer nothing."""

    records = nist_cccbdb.snapshot_records()
    clf3 = next(record for record in records if record.identity.formula == "ClF3")
    monkeypatch.setattr(nist_cccbdb, "snapshot_records", lambda: (clf3, clf3.model_copy(update={"id": "duplicate"})))
    result = NistCccbdbProvider().fetch(GeometryQuery(formula="ClF3", charge=0, atom_inventory={"Cl": 1, "F": 3}))
    assert result.evidence is None


def test_a_conflicting_strong_identifier_blocks_a_formula_match() -> None:
    """A different InChIKey means a different substance, whatever the formula says."""

    result = NistCccbdbProvider().fetch(GeometryQuery(
        formula="NF3", charge=0, atom_inventory={"N": 1, "F": 3}, inchikey="SOMETHING-ELSE-N",
    ))
    assert result.evidence is None


def test_charge_must_match_before_any_geometry_is_returned() -> None:
    result = NistCccbdbProvider().fetch(GeometryQuery(formula="NF3", charge=1, atom_inventory={"N": 1, "F": 3}))
    assert result.evidence is None
