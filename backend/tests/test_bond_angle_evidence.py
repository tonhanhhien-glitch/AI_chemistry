"""Acceptance coverage for provenance-aware molecule-specific bond angles."""

from copy import deepcopy

from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from app.core.config import settings
from app.main import app
from app.schemas.analysis_schema import AnalysisRequest
from app.schemas.molecule_schema import ExternalServiceState, ExternalServiceStatus, PubChemCandidate
from app.schemas.structure3d_schema import Structure3DAtom, Structure3DBond
from app.geometry import resolver as geometry_resolver
from app.geometry.providers import computed
from app.services import experimental_geometry_service, molecule_resolver, structure3d_service
from app.services.analysis_service import analyze
from app.schemas.geometry_evidence_schema import MolecularGeometryEvidence
from app.services.experimental_geometry_service import experimental_records, match_experimental_geometry
from app.services.molecule_resolver import get_record
from app.services.pubchem_service import PubChemLookupResult, PubChemStructureResult
from app.services.rdkit_service import RDKitResult
from app.services.validation_service import validate_explanation_text

client = TestClient(app)

NCL3_SDF = """Nitrogen trichloride
  VSEPR-AI

  4  3  0  0  0  0            999 V2000
    0.0000    0.0000    0.0000 N   0  0  0  0  0  0  0  0  0  0  0
    0.9000    0.9000    0.9000 Cl  0  0  0  0  0  0  0  0  0  0  0  0
   -0.9000   -0.9000    0.9000 Cl  0  0  0  0  0  0  0  0  0  0  0  0
   -0.9000    0.9000   -0.9000 Cl  0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
  1  3  1  0  0  0  0
  1  4  1  0  0  0  0
M  END
$$$$
"""


def integration_status(service: str, state: ExternalServiceState) -> ExternalServiceStatus:
    return ExternalServiceStatus(service=service, state=state)


def disabled_lookup(_parsed) -> PubChemLookupResult:
    return PubChemLookupResult(candidates=[], status=integration_status("PubChem", ExternalServiceState.DISABLED))


def ncl3_candidate() -> PubChemCandidate:
    return PubChemCandidate(
        id="pubchem:61437", cid=61437, formula="NCl3", charge=0,
        name_vi="Nitơ triclorua", name_en="Nitrogen trichloride",
        canonical_smiles="N(Cl)(Cl)Cl", title="Nitrogen trichloride",
        inchikey="QMRQOQQKFWFQGY-UHFFFAOYSA-N",
    )


@pytest.mark.parametrize(("formula", "expected", "pattern"), [
    ("NF3", 102.37, ("F", "N", "F")),
    ("NH3", 106.67, ("H", "N", "H")),
])
def test_offline_analysis_prefers_nist_experimental_geometry(
    monkeypatch: pytest.MonkeyPatch, formula: str, expected: float, pattern: tuple[str, str, str],
) -> None:
    monkeypatch.setattr(molecule_resolver, "lookup_pubchem_formula", disabled_lookup)
    result = analyze(AnalysisRequest(formula=formula))
    preferred = result.bond_angles.preferred[0]
    assert result.schema_version == "1.1"
    assert (preferred.atom1_element, preferred.center_element, preferred.atom2_element) == pattern
    assert preferred.value_deg == expected
    assert preferred.display_label == f"{expected:.2f}°"
    assert preferred.evidence_type == "experimental"
    assert preferred.is_experimental and not preferred.is_computed
    assert preferred.source_name == "NIST CCCBDB"
    assert preferred.phase == "gas"
    assert result.structure3d.is_experimental
    assert not result.structure3d.is_computed
    assert result.structure3d.source_label == "NIST CCCBDB experimental gas-phase geometry"
    annotation = result.structure3d.angle_annotations[0]
    atoms = {atom.id: atom for atom in result.structure3d.atoms}
    actual = structure3d_service.calculate_angle(
        atoms[annotation.atom1_id], atoms[annotation.center_atom_id], atoms[annotation.atom2_id],
    )
    assert actual == pytest.approx(expected, abs=0.01)
    assert annotation.value_deg == pytest.approx(actual)
    assert all(domain.is_illustrative for domain in result.structure3d.electron_domains if domain.kind == "lone_pair")


def test_nf3_remains_general_deterministic_ax3e(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(molecule_resolver, "lookup_pubchem_formula", disabled_lookup)
    result = analyze(AnalysisRequest(formula="NF3"))
    assert result.molecule.source == "deterministic"
    assert result.vsepr.ax_en == "AX3E"
    assert result.vsepr.molecular_geometry == "trigonal pyramidal"
    assert result.bond_angles.vsepr_prediction[0].display_label == "<109.5°"
    assert result.vsepr.teaching_note_vi.startswith("Cặp electron")
    assert result.vsepr.teaching_note_en.startswith("The lone pair")


@pytest.mark.parametrize(("molecule_id", "notation"), [("nh3", "AX3E"), ("h2o", "AX2E2")])
def test_generic_lone_pair_vsepr_rules_are_inequalities(molecule_id: str, notation: str) -> None:
    result = analyze(AnalysisRequest(molecule_id=molecule_id))
    assert result.vsepr.ax_en == notation
    assert result.bond_angles.vsepr_prediction[0].display_label == "<109.5°"


def test_experimental_snapshot_records_are_complete_and_validated() -> None:
    records = experimental_records()
    assert {record.identity.formula for record in records} == {"NF3", "NH3", "ClF3"}
    for record in records:
        assert record.source.reference and record.source.retrieved_at and record.units == "angstrom"
        # CAS is the identifier CCCBDB is addressed by and the one every record carries.
        assert record.identity.cas_rn and record.identity.atom_inventory
        assert record.evidence_type == "experimental"
        assert record.bond_lengths and record.bond_angles
    malformed = deepcopy(records[0].model_dump(mode="json"))
    malformed["bond_angles"][0]["atom1_id"] = "not-an-atom"
    with pytest.raises(ValidationError, match="unknown atom ids"):
        MolecularGeometryEvidence.model_validate(malformed)


def test_identity_matching_checks_charge_and_rejects_ambiguous_formula(monkeypatch: pytest.MonkeyPatch) -> None:
    nf3 = next(record for record in experimental_records() if record.identity.formula == "NF3")
    identity = {"formula": "NF3", "charge": 0, "atom_inventory": {"N": 1, "F": 3}}
    assert match_experimental_geometry(identity) == nf3
    assert match_experimental_geometry(identity | {"charge": 1}) is None
    duplicate = nf3.model_copy(update={"id": "nf3-duplicate"})
    monkeypatch.setattr(experimental_geometry_service, "experimental_records", lambda: (nf3, duplicate))
    assert experimental_geometry_service.match_experimental_geometry(identity) is None


def test_verified_nh3_curated_identity_is_complete() -> None:
    record = get_record("nh3")
    assert record["pubchem_cid"] == 222
    assert record["inchi"] == "InChI=1S/H3N/h1H3"
    assert record["inchikey"] == "QGZKDVFQNNGYKY-UHFFFAOYSA-N"


def test_pubchem_only_structure_is_computed_not_experimental(monkeypatch: pytest.MonkeyPatch) -> None:
    candidate = ncl3_candidate()
    monkeypatch.setattr(
        molecule_resolver, "lookup_pubchem_formula",
        lambda _parsed: PubChemLookupResult(candidates=[candidate], status=integration_status("PubChem", ExternalServiceState.SUCCESS)),
    )
    monkeypatch.setattr(
        computed, "fetch_pubchem_3d",
        lambda _cid: PubChemStructureResult(data=NCL3_SDF, status=integration_status("PubChem", ExternalServiceState.SUCCESS)),
    )
    monkeypatch.setattr(
        computed, "generate_rdkit_result",
        lambda _smiles: RDKitResult(None, integration_status("RDKit", ExternalServiceState.DISABLED)),
    )
    result = analyze(AnalysisRequest(formula="NCl3"))
    assert result.structure3d.is_computed and not result.structure3d.is_experimental
    assert result.bond_angles.preferred
    assert all(item.evidence_type == "computed_conformer" for item in result.bond_angles.preferred)
    assert all(item.is_computed and not item.is_experimental for item in result.bond_angles.preferred)


def test_no_external_result_falls_back_to_general_vsepr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(molecule_resolver, "lookup_pubchem_formula", disabled_lookup)
    monkeypatch.setattr(geometry_resolver, "experimental_providers", lambda: [])
    monkeypatch.setattr(
        computed, "generate_rdkit_result",
        lambda _smiles: RDKitResult(None, integration_status("RDKit", ExternalServiceState.DISABLED)),
    )
    result = analyze(AnalysisRequest(formula="NCl3"))
    assert result.structure3d.is_illustrative
    assert not result.structure3d.is_experimental
    assert result.bond_angles.preferred[0].evidence_type == "ideal_vsepr"
    assert result.bond_angles.preferred[0].display_label == "<109.5°"


def test_asymmetric_angles_are_not_merged_by_the_old_tolerance() -> None:
    atoms = [
        Structure3DAtom(id="c", element="N", x=0, y=0, z=0),
        Structure3DAtom(id="a", element="F", x=1, y=0, z=0),
        Structure3DAtom(id="b", element="F", x=0, y=1, z=0),
        Structure3DAtom(id="d", element="Cl", x=-0.0087265, y=0.9999619, z=0),
    ]
    bonds = [
        Structure3DBond(atom1_id="c", atom2_id="a", order=1),
        Structure3DBond(atom1_id="c", atom2_id="b", order=1),
        Structure3DBond(atom1_id="c", atom2_id="d", order=1),
    ]
    annotations = structure3d_service._angle_annotations(atoms, bonds, "c", "conformer", "test")
    values = sorted(item.value_deg for item in annotations)
    assert len(values) == 3
    assert values == pytest.approx([0.5, 90.0, 90.5], abs=0.01)
    assert all(item.equivalent_count == 1 for item in annotations)


def test_chat_and_explanation_work_for_deterministic_nf3(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(molecule_resolver, "lookup_pubchem_formula", disabled_lookup)
    monkeypatch.setattr(settings, "ENABLE_OPENROUTER", False)
    chat = client.post("/api/v1/chat", json={
        "molecule_id": "deterministic:nf3", "formula": "NF3",
        "messages": [{"role": "user", "content": "What is the angle?"}], "language": "en",
    })
    explanation = client.post("/api/v1/explain", json={
        "molecule_id": "deterministic:nf3", "formula": "NF3", "language": "en",
    })
    assert chat.status_code == 200
    assert "102.37°" in chat.json()["reply"] and "<109.5°" in chat.json()["reply"]
    assert explanation.status_code == 200
    prose = " ".join(explanation.json()["sections"].values())
    assert "102.37°" in prose and "<109.5°" in prose


def test_chat_and_explanation_work_for_pubchem_nf3(monkeypatch: pytest.MonkeyPatch) -> None:
    candidate = PubChemCandidate(
        id="pubchem:24553", cid=24553, formula="NF3", charge=0,
        name_vi="Nitơ triflorua", name_en="Nitrogen trifluoride",
        canonical_smiles="N(F)(F)F", title="Nitrogen trifluoride",
        inchikey="GVGCUCJTUSOZKP-UHFFFAOYSA-N",
    )
    monkeypatch.setattr(
        molecule_resolver, "lookup_pubchem_formula",
        lambda _parsed: PubChemLookupResult(candidates=[candidate], status=integration_status("PubChem", ExternalServiceState.SUCCESS)),
    )
    monkeypatch.setattr(settings, "ENABLE_OPENROUTER", False)
    payload = {"molecule_id": "pubchem:24553", "formula": "NF3", "pubchem_cid": 24553, "language": "en"}
    chat = client.post("/api/v1/chat", json=payload | {"messages": [{"role": "user", "content": "Angle?"}]})
    explanation = client.post("/api/v1/explain", json=payload)
    assert chat.status_code == 200 and "102.37°" in chat.json()["reply"]
    assert explanation.status_code == 200 and "102.37°" in " ".join(explanation.json()["sections"].values())


def test_explanation_validation_allows_evidence_values_but_rejects_invention(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(molecule_resolver, "lookup_pubchem_formula", disabled_lookup)
    result = analyze(AnalysisRequest(formula="NF3"))
    _resolved, record = molecule_resolver.resolve_molecule(
        molecule_resolver.parse_formula("NF3"),
    )
    record["_bond_angles"] = result.bond_angles.model_dump()
    facts = (
        "NF3 has 26 valence electrons; formal charges sum to 0; 3 bonding domains; "
        "1 lone-pair domain; AX3E; tetrahedral; trigonal pyramidal; angles 102.37° and 109.5°."
    )
    valid, problems = validate_explanation_text(facts, record)
    assert valid, problems
    valid, problems = validate_explanation_text(facts + " It is also 111°.", record)
    assert not valid and "contradictory_angle" in problems
