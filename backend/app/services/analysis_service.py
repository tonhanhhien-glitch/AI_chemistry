"""Orchestrate the deterministic offline-first analysis pipeline."""

from app.schemas.analysis_schema import AnalysisNotices, AnalysisRequest, AnalysisResponse
from app.services.ai_explanation_service import generate_explanation
from app.services.formula_parser import parse_formula
from app.services.lewis_service import build_lewis_structure
from app.services.molecule_resolver import get_record, resolve_molecule
from app.services.property_service import get_properties
from app.services.structure3d_service import get_structure3d
from app.services.vsepr_engine import analyze_vsepr


def analyze(request: AnalysisRequest) -> AnalysisResponse:
    if request.molecule_id:
        selected = get_record(request.molecule_id)
        parsed = parse_formula(request.formula or selected["formula"])
    else:
        parsed = parse_formula(request.formula or "")
    molecule, record = resolve_molecule(parsed, request.molecule_id)
    lewis = build_lewis_structure(record)
    vsepr = analyze_vsepr(record)
    structure3d = get_structure3d(record)
    explanation = None
    if request.include_explanation:
        explanation = generate_explanation(record, request.explanation_level, request.language)
    warnings = []
    if structure3d.warning_vi:
        warnings.append(structure3d.warning_vi)
    if "pending_expert" in record["review_status"]:
        warnings.append("Bản ghi thuộc bộ golden nội bộ và đang chờ biên bản ký duyệt của chuyên gia hoá học bên ngoài.")
    return AnalysisResponse(
        molecule=molecule, lewis=lewis, vsepr=vsepr,
        properties=get_properties(record), structure3d=structure3d,
        explanation=explanation,
        notices=AnalysisNotices(warnings_vi=warnings),
    )
