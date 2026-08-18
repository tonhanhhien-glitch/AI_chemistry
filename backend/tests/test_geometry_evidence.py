"""Experimental-first geometry: multi-angle records, constraint fitting, provider priority."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from app.geometry import resolver as geometry_resolver
from app.geometry.fitter import (
    angle_degrees,
    dihedral_degrees,
    distance,
    fit_cartesian_coordinates,
)
from app.geometry.providers.base import GeometryQuery
from app.geometry.providers.computed import PubChemGeometryProvider, RdkitGeometryProvider
from app.geometry.providers.ideal_vsepr import IdealVseprProvider
from app.geometry.providers.nist_cccbdb import NistCccbdbProvider, snapshot_records
from app.geometry.resolver import resolve_geometry
from app.schemas.analysis_schema import AnalysisRequest
from app.schemas.geometry_evidence_schema import (
    BondAngleObservation,
    BondLengthObservation,
    DihedralObservation,
    GeometryAtom,
    GeometryEvidenceType,
    GeometryIdentity,
    GeometrySource,
    MolecularGeometryEvidence,
)
from app.schemas.molecule_schema import ExternalServiceState
from app.services.analysis_service import analyze
from app.services.molecule_resolver import get_record
from app.services.structure3d_service import calculate_angle, resolve_structure3d

FIXTURES = Path(__file__).parent / "fixtures"


def measured_angles(structure) -> dict[str, float]:
    """Recompute every annotated angle straight from the coordinates being rendered."""

    atoms = {atom.id: atom for atom in structure.atoms}
    return {
        annotation.id: calculate_angle(atoms[annotation.atom1_id], atoms[annotation.center_atom_id], atoms[annotation.atom2_id])
        for annotation in structure.angle_annotations
    }


# --------------------------------------------------------------------------- #
# Multi-angle experimental records
# --------------------------------------------------------------------------- #


def test_snapshot_holds_multiple_inequivalent_angles_per_record() -> None:
    clf3 = next(record for record in snapshot_records() if record.identity.formula == "ClF3")
    assert len(clf3.bond_angles) == 3
    assert sorted({observation.value_deg for observation in clf3.bond_angles}) == [87.45, 174.9]
    assert sorted({observation.value_angstrom for observation in clf3.bond_lengths}) == [1.597, 1.697]
    assert clf3.point_group == "C2v"
    assert clf3.phase == "gas"
    assert clf3.source.name == "NIST CCCBDB"
    assert clf3.source.reference and clf3.source.url and clf3.source.retrieved_at
    # Published as internal coordinates only: the fitter has to produce the Cartesians.
    assert clf3.coordinates is None


def test_evidence_model_rejects_observations_referencing_unknown_atoms() -> None:
    with pytest.raises(ValueError, match="unknown atom ids"):
        MolecularGeometryEvidence(
            id="bad", identity=GeometryIdentity(formula="XY2", charge=0),
            evidence_type=GeometryEvidenceType.EXPERIMENTAL,
            atoms=[GeometryAtom(id="a0", element="O", role="center"), GeometryAtom(id="a1", element="H")],
            bond_angles=[BondAngleObservation(id="x", atom1_id="a1", center_atom_id="a0", atom2_id="ghost", value_deg=90.0)],
            source=GeometrySource(name="test"),
        )


# --------------------------------------------------------------------------- #
# ClF3: the mandated regression case
# --------------------------------------------------------------------------- #


def test_clf3_resolves_to_experimental_geometry_with_both_angles() -> None:
    result = analyze(AnalysisRequest(molecule_id="clf3"))
    structure = result.structure3d

    assert structure.is_experimental and not structure.is_computed and not structure.is_illustrative
    assert structure.evidence_type is GeometryEvidenceType.EXPERIMENTAL
    assert structure.geometry_evidence is not None
    assert structure.geometry_evidence.source_name == "NIST CCCBDB"

    grouped = {annotation.display_label: annotation.equivalent_count for annotation in structure.angle_annotations}
    assert grouped == {"87.45°": 2, "174.90°": 1}


def test_clf3_rendered_coordinates_reproduce_both_angles_within_tolerance() -> None:
    """The mandated check: the coordinates the viewer draws must hold the measured angles."""

    structure = analyze(AnalysisRequest(molecule_id="clf3")).structure3d
    measured = measured_angles(structure)
    for annotation in structure.angle_annotations:
        assert annotation.value_deg is not None
        assert measured[annotation.id] == pytest.approx(annotation.value_deg, abs=0.05)
    assert sorted(round(value, 2) for value in measured.values()) == [87.45, 174.9]


def test_clf3_is_no_longer_forced_onto_the_ideal_ax3e2_template() -> None:
    structure = analyze(AnalysisRequest(molecule_id="clf3")).structure3d
    values = sorted(measured_angles(structure).values())
    assert all(abs(value - 90.0) > 1.0 for value in values)
    assert all(abs(value - 180.0) > 1.0 for value in values)


def test_clf3_keeps_the_ideal_vsepr_values_as_secondary_information() -> None:
    result = analyze(AnalysisRequest(molecule_id="clf3"))
    assert result.vsepr.ax_en == "AX3E2"
    assert result.bond_angles.vsepr_prediction[0].display_label == "~90°, 180°"
    assert result.bond_angles.vsepr_prediction[0].evidence_type == "ideal_vsepr"
    # ...but the preferred evidence is the measurement, not the idealization.
    assert [item.display_label for item in result.bond_angles.preferred] == ["87.45°", "174.90°"]
    assert all(item.evidence_type == "experimental" for item in result.bond_angles.preferred)


def test_clf3_bond_lengths_are_grouped_with_equivalent_counts() -> None:
    summary = analyze(AnalysisRequest(molecule_id="clf3")).structure3d.geometry_evidence
    assert summary is not None
    grouped = {item.label: (item.value_angstrom, item.equivalent_count) for item in summary.bond_lengths}
    assert grouped == {"Cl–F axial": (1.697, 2), "Cl–F equatorial": (1.597, 1)}


# --------------------------------------------------------------------------- #
# Constraint fitting and validation
# --------------------------------------------------------------------------- #


def _evidence(**overrides) -> MolecularGeometryEvidence:
    payload = {
        "id": "test", "identity": GeometryIdentity(formula="ClF3", charge=0),
        "evidence_type": GeometryEvidenceType.EXPERIMENTAL,
        "atoms": [
            GeometryAtom(id="a0", element="Cl", role="center"),
            GeometryAtom(id="a1", element="F", role="ligand"),
            GeometryAtom(id="a2", element="F", role="ligand"),
            GeometryAtom(id="a3", element="F", role="ligand"),
        ],
        "bond_lengths": [
            BondLengthObservation(id="r1", atom1_id="a0", atom2_id="a1", value_angstrom=1.698),
            BondLengthObservation(id="r2", atom1_id="a0", atom2_id="a2", value_angstrom=1.698),
            BondLengthObservation(id="r3", atom1_id="a0", atom2_id="a3", value_angstrom=1.598),
        ],
        "bond_angles": [
            BondAngleObservation(id="t1", atom1_id="a1", center_atom_id="a0", atom2_id="a3", value_deg=87.45),
            BondAngleObservation(id="t2", atom1_id="a2", center_atom_id="a0", atom2_id="a3", value_deg=87.45),
            BondAngleObservation(id="t3", atom1_id="a1", center_atom_id="a0", atom2_id="a2", value_deg=174.9),
        ],
        "source": GeometrySource(name="test"),
    }
    payload.update(overrides)
    return MolecularGeometryEvidence(**payload)


def test_fitter_satisfies_every_length_and_angle_constraint_simultaneously() -> None:
    result = fit_cartesian_coordinates(_evidence())
    assert result.accepted and result.coordinates is not None
    points = {item.id: (item.x, item.y, item.z) for item in result.coordinates}
    assert distance(points["a0"], points["a1"]) == pytest.approx(1.698, abs=1e-6)
    assert distance(points["a0"], points["a3"]) == pytest.approx(1.598, abs=1e-6)
    assert angle_degrees(points["a1"], points["a0"], points["a3"]) == pytest.approx(87.45, abs=1e-6)
    assert angle_degrees(points["a1"], points["a0"], points["a2"]) == pytest.approx(174.9, abs=1e-6)
    assert result.max_angle_deviation < 0.001


def test_fitter_handles_dihedral_constraints() -> None:
    """A four-atom chain with a torsion, i.e. the case a star template cannot express."""

    evidence = MolecularGeometryEvidence(
        id="h2o2", identity=GeometryIdentity(formula="H2O2", charge=0),
        evidence_type=GeometryEvidenceType.EXPERIMENTAL,
        atoms=[
            GeometryAtom(id="o1", element="O"), GeometryAtom(id="o2", element="O"),
            GeometryAtom(id="h3", element="H"), GeometryAtom(id="h4", element="H"),
        ],
        bond_lengths=[
            BondLengthObservation(id="r1", atom1_id="o1", atom2_id="o2", value_angstrom=1.475),
            BondLengthObservation(id="r2", atom1_id="o1", atom2_id="h3", value_angstrom=0.950),
            BondLengthObservation(id="r3", atom1_id="o2", atom2_id="h4", value_angstrom=0.950),
        ],
        bond_angles=[
            BondAngleObservation(id="t1", atom1_id="o2", center_atom_id="o1", atom2_id="h3", value_deg=94.8),
            BondAngleObservation(id="t2", atom1_id="o1", center_atom_id="o2", atom2_id="h4", value_deg=94.8),
        ],
        dihedrals=[DihedralObservation(id="d1", atom1_id="h3", atom2_id="o1", atom3_id="o2", atom4_id="h4", value_deg=111.5)],
        source=GeometrySource(name="test"),
    )
    result = fit_cartesian_coordinates(evidence)
    assert result.accepted and result.coordinates is not None
    points = {item.id: (item.x, item.y, item.z) for item in result.coordinates}
    assert abs(dihedral_degrees(points["h3"], points["o1"], points["o2"], points["h4"])) == pytest.approx(111.5, abs=0.01)
    assert angle_degrees(points["o2"], points["o1"], points["h3"]) == pytest.approx(94.8, abs=0.01)


def test_fitter_rejects_geometrically_impossible_constraints() -> None:
    """Two 5 deg angles cannot coexist with a 175 deg angle between the same ligands."""

    impossible = _evidence(bond_angles=[
        BondAngleObservation(id="t1", atom1_id="a1", center_atom_id="a0", atom2_id="a3", value_deg=5.0),
        BondAngleObservation(id="t2", atom1_id="a2", center_atom_id="a0", atom2_id="a3", value_deg=5.0),
        BondAngleObservation(id="t3", atom1_id="a1", center_atom_id="a0", atom2_id="a2", value_deg=174.9),
    ])
    result = fit_cartesian_coordinates(impossible)
    assert not result.accepted
    assert result.coordinates is None
    assert result.rejection_reason and "do not reproduce" in result.rejection_reason


def test_fitter_validates_published_cartesian_coordinates_against_the_observations() -> None:
    """A published coordinate block that contradicts its own angles must be refused."""

    nf3 = next(record for record in snapshot_records() if record.identity.formula == "NF3")
    tampered = nf3.model_copy(update={
        "bond_angles": [
            observation.model_copy(update={"value_deg": 111.0}) for observation in nf3.bond_angles
        ],
        "bond_lengths": [],
    })
    result = fit_cartesian_coordinates(tampered, max_iterations=0)
    assert not result.accepted


def test_rejected_evidence_falls_through_to_the_next_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    """A source whose own numbers cannot be reproduced must not reach the screen."""

    broken = _evidence(bond_angles=[
        BondAngleObservation(id="t1", atom1_id="a1", center_atom_id="a0", atom2_id="a3", value_deg=5.0),
        BondAngleObservation(id="t2", atom1_id="a2", center_atom_id="a0", atom2_id="a3", value_deg=5.0),
        BondAngleObservation(id="t3", atom1_id="a1", center_atom_id="a0", atom2_id="a2", value_deg=174.9),
    ])

    class BrokenProvider:
        name = "broken"
        service = "NIST CCCBDB"

        def fetch(self, _query):
            from app.geometry.providers.base import GeometryProviderResult, provider_status

            return GeometryProviderResult(broken, provider_status(self.service, ExternalServiceState.SUCCESS))

    monkeypatch.setattr(geometry_resolver, "experimental_providers", lambda: [BrokenProvider()])
    geometry = resolve_geometry(GeometryQuery.from_record(get_record("clf3")))
    assert geometry.is_ideal
    assert geometry.rejected and "broken" in geometry.rejected[0]


# --------------------------------------------------------------------------- #
# Provider priority
# --------------------------------------------------------------------------- #


def test_resolution_priority_is_experimental_then_computed_then_ideal(monkeypatch: pytest.MonkeyPatch) -> None:
    record = get_record("nh3")
    assert resolve_geometry(GeometryQuery.from_record(record)).provider_name == "nist_cccbdb"

    monkeypatch.setattr(geometry_resolver, "experimental_providers", lambda: [])
    from app.geometry.providers import computed

    monkeypatch.setattr(computed, "fetch_pubchem_3d", lambda _cid: _pubchem_miss())
    monkeypatch.setattr(computed, "generate_rdkit_result", lambda _smiles: _rdkit_miss())
    assert resolve_geometry(GeometryQuery.from_record(record)).provider_name == "ideal_vsepr"


def _pubchem_miss():
    from app.services.pubchem_service import PubChemStructureResult
    from app.schemas.molecule_schema import ExternalServiceStatus

    return PubChemStructureResult(status=ExternalServiceStatus(service="PubChem", state=ExternalServiceState.CONFORMER_UNAVAILABLE))


def _rdkit_miss():
    from app.services.rdkit_service import RDKitResult
    from app.schemas.molecule_schema import ExternalServiceStatus

    return RDKitResult(None, ExternalServiceStatus(service="RDKit", state=ExternalServiceState.DISABLED))


def test_computed_providers_are_never_labelled_experimental() -> None:
    assert PubChemGeometryProvider().name == "pubchem_3d"
    assert RdkitGeometryProvider().name == "rdkit_etkdg"
    record = get_record("h2o")
    result = IdealVseprProvider().fetch(GeometryQuery.from_record(record))
    assert result.evidence is not None
    assert result.evidence.evidence_type is GeometryEvidenceType.IDEAL_VSEPR
    assert not result.evidence.is_experimental


def test_geometry_stage_falls_back_locally_when_the_budget_is_exhausted() -> None:
    """A NIST/PubChem stall must never make local analysis fail."""

    record = get_record("clf3")
    geometry = resolve_geometry(GeometryQuery.from_record(record), budget_seconds=-1.0)
    assert geometry.is_ideal
    assert any(status.state is ExternalServiceState.TIMEOUT for status in geometry.statuses)


def test_every_curated_species_renders_coordinates_that_match_its_annotations() -> None:
    """Whatever provider wins, the annotation and the drawn geometry must agree."""

    from app.services.molecule_resolver import curated_records

    for record in curated_records():
        structure = resolve_structure3d(record).structure
        measured = measured_angles(structure)
        for annotation in structure.angle_annotations:
            assert annotation.value_deg is not None
            assert measured[annotation.id] == pytest.approx(annotation.value_deg, abs=0.05)
            assert annotation.coordinate_value_deg == pytest.approx(measured[annotation.id], abs=1e-9)


def test_equivalent_angle_counts_sum_to_every_ligand_pair() -> None:
    from app.services.molecule_resolver import curated_records

    for record in curated_records():
        structure = resolve_structure3d(record).structure
        ligands = int(record["bonding_domains"])
        expected_pairs = ligands * (ligands - 1) // 2
        assert sum(annotation.equivalent_count for annotation in structure.angle_annotations) == expected_pairs


def test_near_linear_angle_is_measurable_without_a_degenerate_cross_product() -> None:
    """XeF2 is exactly linear; its 180 deg annotation must still be produced."""

    structure = resolve_structure3d(get_record("xef2")).structure
    assert [round(value, 1) for value in measured_angles(structure).values()] == [180.0]
    assert math.isclose(structure.angle_annotations[0].value_deg or 0.0, 180.0, abs_tol=0.05)
