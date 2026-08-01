"""POST /explain — regenerate prose from immutable resolved facts."""

from fastapi import APIRouter
from app.schemas.explanation_schema import ExplanationRequest, ExplanationResponse
from app.services.ai_explanation_service import generate_explanation
from app.services.bond_angle_service import build_bond_angles
from app.services.molecule_resolver import resolve_request_record
from app.services.structure3d_service import resolve_structure3d

router = APIRouter()


@router.post("/explain", response_model=ExplanationResponse)
def post_explain(request: ExplanationRequest) -> ExplanationResponse:
    record = resolve_request_record(request.molecule_id, request.formula, request.pubchem_cid)
    structure = resolve_structure3d(record).structure
    record["_bond_angles"] = build_bond_angles(record, structure).model_dump()
    return generate_explanation(record, request.level, request.language)
