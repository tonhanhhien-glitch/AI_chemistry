"""POST /explain — regenerate prose from immutable curated facts."""

from fastapi import APIRouter

from app.schemas.explanation_schema import ExplanationRequest, ExplanationResponse
from app.services.ai_explanation_service import generate_explanation
from app.services.molecule_resolver import get_record

router = APIRouter()


@router.post("/explain", response_model=ExplanationResponse)
def post_explain(request: ExplanationRequest) -> ExplanationResponse:
    return generate_explanation(get_record(request.molecule_id), request.level, request.language)
