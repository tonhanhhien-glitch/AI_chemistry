"""Orchestrate the curated-first deterministic analysis pipeline."""

from app.schemas.analysis_schema import AnalysisNotices, AnalysisRequest, AnalysisResponse
from app.schemas.molecule_schema import ExternalServiceState, ExternalServiceStatus
from app.services.ai_explanation_service import generate_explanation
from app.services.bond_angle_service import build_bond_angles
from app.services.formula_parser import parse_formula
from app.services.lewis_service import build_lewis_structure
from app.services.molecule_resolver import get_record, resolve_molecule
from app.services.property_service import get_properties
from app.services.structure3d_service import resolve_structure3d
from app.services.vsepr_engine import analyze_vsepr


def _deduplicate_statuses(statuses: list[ExternalServiceStatus]) -> list[ExternalServiceStatus]:
    result: list[ExternalServiceStatus] = []
    for status in statuses:
        if not any(existing.service == status.service and existing.state == status.state for existing in result):
            result.append(status)
    return result


def analyze(request: AnalysisRequest) -> AnalysisResponse:
    if request.molecule_id:
        selected = get_record(request.molecule_id)
        parsed = parse_formula(request.formula or selected["formula"])
    else:
        parsed = parse_formula(request.formula or "")
    molecule, record = resolve_molecule(parsed, request.molecule_id, request.pubchem_cid)
    lewis = build_lewis_structure(record)
    vsepr = analyze_vsepr(record)
    structure_result = resolve_structure3d(record)
    structure3d = structure_result.structure
    bond_angles = build_bond_angles(record, structure3d)
    record["_bond_angles"] = bond_angles.model_dump()
    explanation = None
    if request.include_explanation:
        explanation = generate_explanation(record, request.explanation_level, request.language)

    warnings_vi = [structure3d.warning_vi] if structure3d.warning_vi else []
    warnings_en = [structure3d.warning_en] if structure3d.warning_en else []
    if "pending_expert" in record["review_status"]:
        warnings_vi.append("Bản ghi chuẩn nội bộ này đang chờ chuyên gia hóa học ký duyệt bên ngoài.")
        warnings_en.append("This internal golden record is awaiting external chemistry-expert sign-off.")
    if record["source"] == "PubChem reference":
        warnings_vi.append("Danh tính PubChem đã được kiểm tra; suy luận Lewis/VSEPR tất định chưa được chuyên gia tuyển chọn.")
        warnings_en.append("PubChem identity was validated; deterministic Lewis/VSEPR inference is not expert-curated.")
    elif record["source"] == "deterministic":
        warnings_vi.append("Cấu trúc thuộc phạm vi công thức một tâm duy nhất; kết quả tất định chưa được chuyên gia tuyển chọn.")
        warnings_en.append("The formula has a unique supported single-center form; the deterministic result is not expert-curated.")

    statuses = _deduplicate_statuses([
        *record.get("_external_service_statuses", []),
        *structure_result.statuses,
    ])
    external_services_used: list[str] = []
    if record["source"] == "PubChem reference" or structure3d.source.value == "pubchem_3d":
        external_services_used.append("PubChem")
    if structure3d.source.value == "rdkit_etkdg":
        external_services_used.append("RDKit")
    return AnalysisResponse(
        molecule=molecule,
        lewis=lewis,
        vsepr=vsepr,
        properties=get_properties(record),
        structure3d=structure3d,
        bond_angles=bond_angles,
        explanation=explanation,
        notices=AnalysisNotices(
            offline_capable=record["source"] != "PubChem reference",
            external_services_used=external_services_used,
            warnings_vi=warnings_vi,
            warnings_en=warnings_en,
            external_service_statuses=statuses,
        ),
    )
