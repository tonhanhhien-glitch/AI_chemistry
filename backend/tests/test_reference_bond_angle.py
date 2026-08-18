"""The 3D model must draw each molecule's own bond angle, not the generic AXnEm ideal."""

import math

import pytest

from app.schemas.analysis_schema import AnalysisRequest
from app.schemas.molecule_schema import ExternalServiceState, ExternalServiceStatus
from app.geometry.providers import computed
from app.services import molecule_resolver, structure3d_service
from app.services.analysis_service import analyze
from app.services.pubchem_service import PubChemLookupResult
from app.services.rdkit_service import RDKitResult
from app.services.structure3d_service import calculate_angle


@pytest.fixture(autouse=True)
def offline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin every case to the offline path so the assertions describe local data only."""

    monkeypatch.setattr(
        molecule_resolver, "lookup_pubchem_formula",
        lambda _parsed: PubChemLookupResult(candidates=[], status=ExternalServiceStatus(service="PubChem", state=ExternalServiceState.DISABLED)),
    )
    monkeypatch.setattr(
        computed, "generate_rdkit_result",
        lambda _smiles: RDKitResult(None, ExternalServiceStatus(service="RDKit", state=ExternalServiceState.DISABLED)),
    )


def bond_pairs(structure) -> list[tuple[str, str]]:
    elements = {atom.id: atom.element for atom in structure.atoms}
    return sorted(tuple(sorted((elements[bond.atom1_id], elements[bond.atom2_id]))) for bond in structure.bonds)


def measured_angles(structure) -> list[float]:
    atoms = {atom.id: atom for atom in structure.atoms}
    return [
        calculate_angle(atoms[item.atom1_id], atoms[item.center_atom_id], atoms[item.atom2_id])
        for item in structure.angle_annotations
    ]


@pytest.mark.parametrize(("molecule_id", "notation", "geometry", "bonds", "angle"), [
    ("h2o", "AX2E2", "bent", [("H", "O"), ("H", "O")], 104.5),
    ("nh3", "AX3E", "trigonal pyramidal", [("H", "N")] * 3, 106.67),
    ("ch4", "AX4", "tetrahedral", [("C", "H")] * 4, 109.5),
])
def test_molecule_specific_angle_is_drawn_not_the_electron_domain_ideal(
    molecule_id: str, notation: str, geometry: str, bonds: list[tuple[str, str]], angle: float,
) -> None:
    result = analyze(AnalysisRequest(molecule_id=molecule_id))
    structure = result.structure3d

    assert result.vsepr.ax_en == notation
    assert result.vsepr.molecular_geometry == geometry
    assert len(structure.atoms) == len(bonds) + 1
    assert bond_pairs(structure) == sorted(bonds)

    # The arc is measured from the coordinates, so the model itself has to hold the angle.
    assert measured_angles(structure) == pytest.approx([angle], abs=0.05)
    assert structure.angle_annotations[0].value_deg == pytest.approx(angle, abs=0.05)
    assert structure.reference_bond_angle is not None
    assert structure.reference_bond_angle.value_deg == pytest.approx(angle, abs=0.05)
    # Header and 3D overlay resolve the same molecule-specific value.
    assert result.bond_angles.preferred[0].value_deg == pytest.approx(angle, abs=0.05)


@pytest.mark.parametrize(("molecule_id", "category"), [
    # H2O and CH4 now have local NIST CCCBDB experimental-geometry snapshots too, so
    # they resolve to "measured" the same way NH3 already did.
    ("h2o", "measured"), ("nh3", "measured"), ("ch4", "measured"),
])
def test_reference_angle_records_where_the_value_came_from(molecule_id: str, category: str) -> None:
    reference = analyze(AnalysisRequest(molecule_id=molecule_id)).structure3d.reference_bond_angle
    assert reference is not None and reference.category == category


@pytest.mark.parametrize("molecule_id", ["h2o", "nh3"])
def test_lone_pair_geometries_never_show_the_tetrahedral_ideal(molecule_id: str) -> None:
    result = analyze(AnalysisRequest(molecule_id=molecule_id))
    assert result.vsepr.electron_geometry == "tetrahedral"
    assert result.vsepr.ideal_angle == "<109.5°"          # the generic electron-domain rule survives
    assert all(round(value, 1) != 109.5 for value in measured_angles(result.structure3d))
    assert result.bond_angles.preferred[0].display_label != "<109.5°"


def test_water_keeps_two_bonds_and_two_illustrative_lone_pair_domains() -> None:
    structure = analyze(AnalysisRequest(molecule_id="h2o")).structure3d
    bonding = [domain for domain in structure.electron_domains if domain.kind == "bonding"]
    lone_pairs = [domain for domain in structure.electron_domains if domain.kind == "lone_pair"]
    assert len(structure.bonds) == 2 and len(bonding) == 2 and len(lone_pairs) == 2
    assert all(domain.is_illustrative for domain in lone_pairs)
    # The lone-pair overlay is separate from connectivity: the bonding domains still point
    # along the two real O-H bonds, so nothing about the lobes can stand in for a bond.
    atoms = {atom.id: atom for atom in structure.atoms}
    for domain, bond in zip(bonding, structure.bonds, strict=True):
        ligand = atoms[bond.atom2_id]
        length = math.hypot(ligand.x, ligand.y, ligand.z)
        assert (domain.direction.x, domain.direction.y, domain.direction.z) == pytest.approx(
            (ligand.x / length, ligand.y / length, ligand.z / length),
        )


def test_generic_vsepr_angle_is_used_when_no_molecule_specific_value_exists() -> None:
    """H2S has neither an experimental record nor a curated angle, so it keeps the ideal."""

    result = analyze(AnalysisRequest(formula="H2S"))
    reference = result.structure3d.reference_bond_angle
    assert reference is not None
    assert (reference.category, reference.value_deg) == ("ideal_vsepr", 109.5)
    assert measured_angles(result.structure3d) == pytest.approx([109.5], abs=0.05)
    assert result.bond_angles.preferred[0].evidence_type == "ideal_vsepr"


@pytest.mark.parametrize(("molecule_id", "bonds", "angles"), [
    # CO2, BF3, PCl5 and SF6 now resolve via experimental evidence too, but their
    # D_inf_h/D3h/Oh symmetry keeps the measured angles numerically identical to the
    # idealized template. NO3- has neither an experimental record nor a curated
    # molecule-specific override, so it still renders from the plain ideal template.
    ("co2", 2, [180.0]), ("bf3", 3, [120.0]), ("no3-minus", 3, [120.0]),
    ("pcl5", 5, [90.0, 120.0, 180.0]), ("sf6", 6, [90.0, 180.0]),
])
def test_geometries_without_one_reference_angle_keep_their_template(
    molecule_id: str, bonds: int, angles: list[float],
) -> None:
    structure = analyze(AnalysisRequest(molecule_id=molecule_id)).structure3d
    assert len(structure.bonds) == bonds
    assert sorted(measured_angles(structure)) == pytest.approx(angles, abs=0.05)


@pytest.mark.parametrize(("ax_en", "target"), [
    ("AX2E2", 104.5), ("AX2E2", 92.0), ("AX3E", 107.0), ("AX2E", 118.0),
])
def test_reshape_moves_every_equivalent_ligand_pair_onto_the_target(ax_en: str, target: float) -> None:
    template = structure3d_service._templates()[ax_en]["ligands"]
    shaped = structure3d_service._reshape_ligands([tuple(vector) for vector in template], target)
    assert shaped is not None
    for first in range(len(shaped)):
        for second in range(first + 1, len(shaped)):
            cosine = sum(left * right for left, right in zip(shaped[first], shaped[second], strict=True))
            assert math.degrees(math.acos(cosine)) == pytest.approx(target, abs=0.01)
            assert math.hypot(*shaped[first]) == pytest.approx(1.0)


@pytest.mark.parametrize("ax_en", ["AX2", "AX3", "AX4", "AX5", "AX4E", "AX5E", "AX6", "AX4E2"])
def test_reshape_declines_templates_without_one_symmetric_angle(ax_en: str) -> None:
    template = structure3d_service._templates()[ax_en]["ligands"]
    assert structure3d_service._reshape_ligands([tuple(vector) for vector in template], 100.0) is None
