"""Comprehensive regression and integration tests for Phases 1-7 of the refactor."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
import pytest

from app.core.config import settings
from app.core.exceptions import ChemistryValidationError
from app.geometry.adapters.nist_cccbdb_adapter import parse_cccbdb_geometry_html
from app.geometry.fitter import fit_cartesian_coordinates
from app.geometry.resolver import resolve_geometry
from app.geometry.providers.base import GeometryQuery
from app.properties.providers.base import PropertyQuery
from app.properties.providers.pubchem_view import PubChemViewPropertyProvider
from app.properties.schema import PropertyEvidenceType, PropertyObservation
from app.properties.service import full_properties
from app.schemas.geometry_evidence_schema import GeometryIdentity, MolecularGeometryEvidence
from app.services.chemical_query_resolver import resolve_chemical_query
from app.services.connectivity_service import (
    TopologyResolutionStatus,
    check_formula_topology_eligibility,
    parse_molfile,
    resolve_connectivity,
)
from app.services.deterministic_chemistry_service import build_deterministic_record, solve_structure
from app.services.formula_parser import parse_formula
from app.services.lewis_service import build_lewis_structure
from app.services.pubchem_service import lookup_pubchem_formula


def test_formula_topology_eligibility_accepts_unique_single_centers() -> None:
    for formula_str in ["H2O", "NH3", "SO4^2-", "ClF3", "SF4", "XeF4", "O3", "I3-", "CO2", "NO3-", "CO3^2-"]:
        parsed = parse_formula(formula_str)
        is_eligible, central, status, reason = check_formula_topology_eligibility(parsed)
        assert is_eligible, f"{formula_str} should be uniquely eligible: {reason}"
        assert central is not None
        assert status is TopologyResolutionStatus.UNIQUE_FORMULA_TOPOLOGY


def test_formula_topology_eligibility_rejects_ambiguous_and_multicenter_formulas() -> None:
    # H2O2 has 2 O atoms (multiple multi-valent atoms, chain structure)
    parsed_h2o2 = parse_formula("H2O2")
    is_eligible, _, status, _ = check_formula_topology_eligibility(parsed_h2o2)
    assert not is_eligible
    assert status is TopologyResolutionStatus.AMBIGUOUS

    # N2O has 2 N atoms (ambiguous N-N-O vs N-O-N from formula alone)
    parsed_n2o = parse_formula("N2O")
    is_eligible, _, status, _ = check_formula_topology_eligibility(parsed_n2o)
    assert not is_eligible
    assert status is TopologyResolutionStatus.AMBIGUOUS

    # HNO2 is an oxoacid (H is bonded to O, multi-center)
    parsed_hno2 = parse_formula("HNO2")
    is_eligible, _, status, _ = check_formula_topology_eligibility(parsed_hno2)
    assert not is_eligible
    assert status is TopologyResolutionStatus.AMBIGUOUS


def test_pubchem_2d_molfile_connectivity_without_rdkit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "ENABLE_RDKIT", False)
    # V2000 molfile for water (CID 962)
    molfile = """
  PubChem-08172600002D 

  3  2  0  0  0  0  0  0  0  0999 V2000
    0.0000    0.0000    0.0000 O   0  0  0  0  0  0  0  0  0  0  0  0
    0.8000    0.6000    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
   -0.8000    0.6000    0.0000 H   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
  1  3  1  0  0  0  0
M  END
"""
    result = resolve_connectivity(molfile=molfile)
    assert result.graph is not None
    assert result.graph.source == "molfile"
    assert result.graph.single_center_id("O") == "a0"
    assert len(result.graph.bonds) == 2


def test_chemical_query_resolver_distinguishes_formula_from_name() -> None:
    # Formula input
    res_formula = resolve_chemical_query("SO4^2-")
    assert res_formula.kind == "formula"
    assert res_formula.parsed.formula == "SO4^2-"

    # Name input with capitalized first letter (must not be mistaken for element W tungsten!)
    res_name = resolve_chemical_query("Water")
    assert res_name.kind == "name"
    assert res_name.parsed.formula == "H2O"


def test_resonance_individual_structures_are_preserved() -> None:
    parsed = parse_formula("SO4^2-")
    record = build_deterministic_record(parsed)
    assert record["resonance_forms"] == 6
    assert len(record["resonance_structures"]) == 6

    # Verify that the 6 forms represent distinct bond order assignments
    bond_assignments = {tuple(f["bond_orders"]) for f in record["resonance_structures"]}
    assert len(bond_assignments) == 6

    # Verify LewisStructure representation
    lewis = build_lewis_structure(record)
    assert len(lewis.resonance_structures) == 6
    assert lewis.resonance_forms == 6


def test_geometry_fitter_prefers_direct_valid_cartesian_coordinates() -> None:
    raw_html = """
    <html><body>
    <h1>Geometry for ClF3</h1>
    <p>Point group C2v</p>
    <h2>Cartesian Coordinates (Angstroms)</h2>
    <table>
      <tr><th>Atom</th><th>X</th><th>Y</th><th>Z</th></tr>
      <tr><td>Cl</td><td>0.000000</td><td>0.000000</td><td>0.000000</td></tr>
      <tr><td>F</td><td>0.075550</td><td>1.696318</td><td>0.000000</td></tr>
      <tr><td>F</td><td>0.075550</td><td>-1.696318</td><td>0.000000</td></tr>
      <tr><td>F</td><td>1.598000</td><td>0.000000</td><td>0.000000</td></tr>
    </table>
    <h2>Bond Lengths (Angstroms)</h2>
    <table>
      <tr><th>Bond</th><th>Length</th></tr>
      <tr><td>Cl1-F2</td><td>1.698</td></tr>
      <tr><td>Cl1-F3</td><td>1.698</td></tr>
      <tr><td>Cl1-F4</td><td>1.598</td></tr>
    </table>
    <h2>Bond Angles (degrees)</h2>
    <table>
      <tr><th>Angle</th><th>Value</th></tr>
      <tr><td>F2-Cl1-F4</td><td>87.45</td></tr>
      <tr><td>F3-Cl1-F4</td><td>87.45</td></tr>
      <tr><td>F2-Cl1-F3</td><td>174.90</td></tr>
    </table>
    </body></html>
    """
    evidence = parse_cccbdb_geometry_html(
        raw_html,
        identity=GeometryIdentity(formula="ClF3", charge=0, atom_inventory={"Cl": 1, "F": 3}),
        source_url="https://example.invalid/clf3",
    )
    assert evidence is not None
    assert evidence.coordinates is not None
    fit = fit_cartesian_coordinates(evidence)
    assert fit.accepted
    assert not fit.coordinates_are_fitted  # Accepted direct valid coordinates!


def test_property_observation_and_source_annotation_classification(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(settings, "ENABLE_PUBCHEM", True)
    monkeypatch.setattr(settings, "ENABLE_PUBCHEM_PROPERTIES", True)

    payload = {
        "Record": {
            "Section": [
                {
                    "TOCHeading": "Physical Description",
                    "Information": [
                        {"Value": {"StringWithMarkup": [{"String": "Colorless gas with a pungent odor."}]}},
                        {"Value": {"StringWithMarkup": [{"String": "Compressed liquefied gas."}]}},
                    ],
                },
                {
                    "TOCHeading": "Melting Point",
                    "Information": [
                        {"Value": {"Number": [-76.3], "Unit": "°C"}, "Reference": ["CRC Handbook"]},
                        {"Value": {"Number": [-83.0], "Unit": "°C"}, "Reference": ["Merck Index"]},
                    ],
                },
            ]
        }
    }

    class _SuccessState:
        value = "success"

    monkeypatch.setattr(
        "app.properties.providers.pubchem_view._request_bytes",
        lambda _url: (json.dumps(payload).encode(), _SuccessState()),
    )

    provider = PubChemViewPropertyProvider()
    query = PropertyQuery(formula="ClF3", charge=0, atom_inventory={"Cl": 1, "F": 3}, pubchem_cid=24637)
    result = provider.fetch(query)

    phys_desc = next(p for p in result.properties if p.key == "physical_description")
    assert phys_desc.evidence_type == PropertyEvidenceType.SOURCE_ANNOTATION
    assert len(phys_desc.observations) == 2

    melting = next(p for p in result.properties if p.key == "melting_point")
    assert melting.evidence_type == PropertyEvidenceType.EXPERIMENTAL
    assert len(melting.observations) == 2
    assert melting.observations[0].source_reference == "CRC Handbook"
    assert melting.observations[1].source_reference == "Merck Index"
