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
    represented = 2 * sum(bond.order for bond in result.lewis.bonds) + 2 * sum(atom.lone_pairs for atom in result.lewis.atoms)
    assert represented == result.lewis.total_valence_electrons
    assert len(result.structure3d.atoms) == len(result.lewis.atoms)
    assert result.structure3d.is_illustrative is True
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
