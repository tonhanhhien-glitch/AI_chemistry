"""Every golden species must conserve electrons and match its VSEPR contract."""

import pytest

from app.schemas.analysis_schema import AnalysisRequest
from app.services.analysis_service import analyze
from app.services.molecule_resolver import curated_records

GOLDEN = [(record["id"], record["formula"], record["ax_en"], record["molecular_geometry"]) for record in curated_records()]


@pytest.mark.parametrize(("molecule_id", "formula", "ax_en", "geometry"), GOLDEN)
def test_complete_golden_pipeline(molecule_id: str, formula: str, ax_en: str, geometry: str) -> None:
    result = analyze(AnalysisRequest(molecule_id=molecule_id, include_explanation=True))
    assert result.molecule.formula == formula
    assert result.vsepr.ax_en == ax_en
    assert result.vsepr.molecular_geometry == geometry
    assert sum(atom.formal_charge for atom in result.lewis.atoms) == result.molecule.charge
    represented = (
        2 * sum(bond.order for bond in result.lewis.bonds)
        + 2 * sum(atom.lone_pairs for atom in result.lewis.atoms)
        + sum(atom.unpaired_electrons for atom in result.lewis.atoms)
    )
    assert represented == result.lewis.total_valence_electrons
    assert len(result.structure3d.atoms) == len(result.lewis.atoms)
    assert result.structure3d.is_illustrative or result.structure3d.is_experimental
    assert all(domain.is_illustrative for domain in result.structure3d.electron_domains if domain.kind == "lone_pair")
    assert result.explanation is not None
    assert result.explanation.facts_validated is True


def test_resonance_and_exception_notes() -> None:
    nitrate = analyze(AnalysisRequest(formula="NO3-"))
    assert nitrate.lewis.resonance_forms == 3
    assert nitrate.lewis.resonance_note_vi
    bf3 = analyze(AnalysisRequest(formula="BF3"))
    assert bf3.lewis.exception_flags.electron_deficient
    sf6 = analyze(AnalysisRequest(formula="SF6"))
    assert sf6.lewis.exception_flags.expanded_octet


@pytest.mark.parametrize(("molecule_id", "lone_pair_domains"), [("no2", 1), ("clo2", 2)])
def test_odd_electron_species_carry_their_unpaired_electron_end_to_end(molecule_id: str, lone_pair_domains: int) -> None:
    result = analyze(AnalysisRequest(molecule_id=molecule_id))
    center = next(atom for atom in result.lewis.atoms if atom.id == result.lewis.central_atom_id)
    assert result.lewis.exception_flags.odd_electron
    assert result.lewis.total_valence_electrons % 2 == 1
    assert center.unpaired_electrons == 1
    assert sum(atom.unpaired_electrons for atom in result.lewis.atoms) == 1
    # The single electron is a VSEPR domain of its own, shown as a one-electron lobe.
    non_bonding = [domain for domain in result.structure3d.electron_domains if domain.kind == "lone_pair"]
    assert len(non_bonding) == lone_pair_domains
    assert sorted(domain.occupancy for domain in non_bonding) == [1] + [2] * (lone_pair_domains - 1)


def test_lewis_rejects_unpaired_electrons_that_do_not_align_with_the_atoms() -> None:
    from app.core.exceptions import ChemistryValidationError
    from app.services.lewis_service import build_lewis_structure
    from app.services.molecule_resolver import get_record

    record = {**get_record("no2"), "unpaired_electrons": [1, 0]}
    with pytest.raises(ChemistryValidationError):
        build_lewis_structure(record)
