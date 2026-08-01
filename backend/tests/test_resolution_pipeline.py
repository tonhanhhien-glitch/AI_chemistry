"""Network-free coverage for PubChem resolution and educational 3D metadata."""

import json
import math
from dataclasses import replace

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.schemas.analysis_schema import AnalysisRequest
from app.schemas.molecule_schema import ExternalServiceState, ExternalServiceStatus, PubChemCandidate
from app.schemas.structure3d_schema import Structure3DAtom, StructureSource
from app.services import molecule_resolver, pubchem_service, structure3d_service
from app.services.analysis_service import analyze
from app.services.formula_parser import parse_formula
from app.services.molecule_resolver import curated_records
from app.services.pubchem_service import PubChemLookupResult, PubChemStructureResult
from app.services.rdkit_service import RDKitResult, RDKitStructure
from app.services.structure3d_service import calculate_angle

client = TestClient(app)

NF3_SDF = """Nitrogen trifluoride
  VSEPR-AI

  4  3  0  0  0  0            999 V2000
    0.0000    0.0000    0.0000 N   0  0  0  0  0  0  0  0  0  0  0  0
    0.9000    0.9000    0.9000 F   0  0  0  0  0  0  0  0  0  0  0  0
   -0.9000   -0.9000    0.9000 F   0  0  0  0  0  0  0  0  0  0  0  0
   -0.9000    0.9000   -0.9000 F   0  0  0  0  0  0  0  0  0  0  0  0
  1  2  1  0  0  0  0
  1  3  1  0  0  0  0
  1  4  1  0  0  0  0
M  END
$$$$
"""
NF3_MOLBLOCK = NF3_SDF.split("$$$$", 1)[0]


def status(service: str, state: ExternalServiceState) -> ExternalServiceStatus:
    return ExternalServiceStatus(service=service, state=state)


def candidate(cid: int = 24553, *, formula: str = "NF3", charge: int = 0) -> PubChemCandidate:
    return PubChemCandidate(
        id=f"pubchem:{cid}", cid=cid, formula=formula, charge=charge,
        name_vi="Nitrogen trifluoride", name_en="Nitrogen trifluoride",
        canonical_smiles="N(F)(F)F", title="Nitrogen trifluoride",
        inchikey=f"NF3-KEY-{cid}",
    )


def lookup(*candidates: PubChemCandidate, state: ExternalServiceState = ExternalServiceState.SUCCESS) -> PubChemLookupResult:
    return PubChemLookupResult(candidates=list(candidates), status=status("PubChem", state))


def patch_identity(monkeypatch: pytest.MonkeyPatch, *candidates: PubChemCandidate) -> None:
    monkeypatch.setattr(molecule_resolver, "lookup_pubchem_formula", lambda _parsed: lookup(*candidates, state=ExternalServiceState.AMBIGUOUS if len(candidates) > 1 else ExternalServiceState.SUCCESS))


def patch_no_external_3d(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(structure3d_service, "fetch_pubchem_3d", lambda _cid: PubChemStructureResult(status=status("PubChem", ExternalServiceState.CONFORMER_UNAVAILABLE)))
    monkeypatch.setattr(structure3d_service, "generate_rdkit_result", lambda _smiles: RDKitResult(None, status("RDKit", ExternalServiceState.DISABLED)))


def test_supported_unique_formula_falls_back_deterministically_when_pubchem_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(molecule_resolver, "lookup_pubchem_formula", lambda _parsed: lookup(state=ExternalServiceState.DISABLED))
    patch_no_external_3d(monkeypatch)
    result = analyze(AnalysisRequest(formula="NF3"))
    assert result.molecule.source == "deterministic"
    assert result.vsepr.ax_en == "AX3E"
    assert result.structure3d.source is StructureSource.CURATED_COORDINATES
    assert result.structure3d.is_experimental
    assert result.notices.external_services_used == []
    assert result.notices.offline_capable is True


def test_nf3_resolves_from_mocked_pubchem_with_3d(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_identity(monkeypatch, candidate())
    monkeypatch.setattr(structure3d_service, "fetch_pubchem_3d", lambda _cid: PubChemStructureResult(data=NF3_SDF, status=status("PubChem", ExternalServiceState.SUCCESS)))
    result = analyze(AnalysisRequest(formula="NF3"))
    assert result.molecule.formula == "NF3"
    assert result.molecule.pubchem_cid == 24553
    assert result.molecule.canonical_identity == "NF3-KEY-24553"
    assert result.vsepr.bonding_domains == 3
    assert result.vsepr.lone_pair_domains == 1
    assert result.vsepr.ax_en == "AX3E"
    assert result.vsepr.molecular_geometry == "trigonal pyramidal"
    assert result.structure3d.format == "coordinates"
    assert result.structure3d.source is StructureSource.CURATED_COORDINATES
    assert result.structure3d.is_experimental
    assert len([domain for domain in result.structure3d.electron_domains if domain.kind == "lone_pair"]) == 1
    assert result.notices.external_services_used == ["PubChem"]
    assert result.notices.offline_capable is False


@pytest.mark.parametrize(("row_formula", "row_charge"), [("NCl3", 0), ("NF3", 1)])
def test_pubchem_formula_or_charge_mismatch_is_rejected(monkeypatch: pytest.MonkeyPatch, tmp_path, row_formula: str, row_charge: int) -> None:
    payload = {"PropertyTable": {"Properties": [{"CID": 1, "MolecularFormula": row_formula, "Charge": row_charge, "ConnectivitySMILES": "N(F)(F)F"}]}}
    monkeypatch.setattr(pubchem_service.settings, "ENABLE_PUBCHEM", True)
    monkeypatch.setattr(pubchem_service.settings, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(pubchem_service, "_request_bytes", lambda _url: (json.dumps(payload).encode(), ExternalServiceState.SUCCESS))
    result = pubchem_service.lookup_pubchem_formula(parse_formula("NF3"))
    assert result.candidates == []
    assert result.status.state is ExternalServiceState.FORMULA_MISMATCH


def test_multiple_valid_pubchem_candidates_return_409(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_identity(monkeypatch, candidate(1), candidate(2))
    response = client.post("/api/v1/analyze", json={"formula": "NF3"})
    assert response.status_code == 409
    candidates = response.json()["detail"]["candidates"]
    assert {item["cid"] for item in candidates} == {1, 2}
    assert all(item["canonical_smiles"] == "N(F)(F)F" for item in candidates)


def test_selected_pubchem_cid_resubmits_without_formula_edit(monkeypatch: pytest.MonkeyPatch) -> None:
    patch_identity(monkeypatch, candidate(1), candidate(2))
    patch_no_external_3d(monkeypatch)
    response = client.post("/api/v1/analyze", json={"formula": "NF3", "pubchem_cid": 2})
    assert response.status_code == 200
    assert response.json()["molecule"]["pubchem_cid"] == 2


def test_pubchem_timeout_is_typed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(molecule_resolver, "lookup_pubchem_formula", lambda _parsed: lookup(state=ExternalServiceState.TIMEOUT))
    response = client.post("/api/v1/analyze", json={"formula": "NF3"})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "EXTERNAL_RESOLUTION_FAILED"
    assert "timeout" in response.json()["detail"]["message"]


def test_rdkit_is_second_structure_priority(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(structure3d_service, "match_experimental_geometry", lambda _record: None)
    patch_identity(monkeypatch, candidate())
    monkeypatch.setattr(structure3d_service, "fetch_pubchem_3d", lambda _cid: PubChemStructureResult(status=status("PubChem", ExternalServiceState.CONFORMER_UNAVAILABLE)))
    monkeypatch.setattr(structure3d_service, "generate_rdkit_result", lambda _smiles: RDKitResult(RDKitStructure(NF3_MOLBLOCK, force_field="UFF"), status("RDKit", ExternalServiceState.SUCCESS)))
    result = analyze(AnalysisRequest(formula="NF3"))
    assert result.structure3d.format == "molblock"
    assert result.structure3d.source is StructureSource.RDKIT_ETKDG
    assert result.structure3d.is_computed and not result.structure3d.is_experimental
    assert result.notices.external_services_used == ["PubChem", "RDKit"]


def test_vsepr_is_final_structure_fallback_and_angles_match(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(structure3d_service, "match_experimental_geometry", lambda _record: None)
    patch_identity(monkeypatch, candidate())
    patch_no_external_3d(monkeypatch)
    result = analyze(AnalysisRequest(formula="NF3"))
    assert result.structure3d.source is StructureSource.IDEALIZED_VSEPR
    annotation = result.structure3d.angle_annotations[0]
    atoms = {atom.id: atom for atom in result.structure3d.atoms}
    actual = calculate_angle(atoms[annotation.atom1_id], atoms[annotation.center_atom_id], atoms[annotation.atom2_id])
    assert annotation.value_deg == pytest.approx(actual)
    assert annotation.display_label == f"{actual:.1f}°"
    assert result.vsepr.reference_angles[0].display_label == "<109.5°"
    assert annotation.display_label != result.vsepr.reference_angles[0].display_label


def test_representative_angle_classes_and_lone_pair_counts() -> None:
    records = {record["id"]: record for record in curated_records()}
    for record in records.values():
        structure = structure3d_service.get_structure3d(record)
        lone_pairs = [domain for domain in structure.electron_domains if domain.kind == "lone_pair"]
        assert len(lone_pairs) == record["lone_pair_domains"]
    pcl5 = structure3d_service.get_structure3d(records["pcl5"])
    assert [annotation.value_deg for annotation in pcl5.angle_annotations] == pytest.approx([90, 120, 180], abs=0.1)
    sf6 = structure3d_service.get_structure3d(records["sf6"])
    assert [annotation.value_deg for annotation in sf6.angle_annotations] == pytest.approx([90, 180], abs=0.1)


def test_curated_notices_do_not_claim_external_service_use() -> None:
    result = analyze(AnalysisRequest(formula="CO2"))
    assert result.notices.external_services_used == []
    assert result.notices.offline_capable is True


def test_calculate_angle_reference_vectors() -> None:
    center = Structure3DAtom(id="c", element="X", x=0, y=0, z=0)
    atom = lambda name, xyz: Structure3DAtom(id=name, element="X", x=xyz[0], y=xyz[1], z=xyz[2])
    assert calculate_angle(atom("a", (1, 0, 0)), center, atom("b", (-1, 0, 0))) == pytest.approx(180)
    assert calculate_angle(atom("a", (1, 0, 0)), center, atom("b", (-0.5, math.sqrt(3) / 2, 0))) == pytest.approx(120)
    assert calculate_angle(atom("a", (1, 1, 1)), center, atom("b", (-1, -1, 1))) == pytest.approx(109.4712206)
    assert calculate_angle(atom("a", (1, 0, 0)), center, atom("b", (0, 1, 0))) == pytest.approx(90)


def test_calculate_angle_rejects_zero_vector() -> None:
    center = Structure3DAtom(id="c", element="X", x=0, y=0, z=0)
    with pytest.raises(ValueError, match="non-zero"):
        calculate_angle(center, center, Structure3DAtom(id="b", element="X", x=1, y=0, z=0))
