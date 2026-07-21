"""POST /analyze — complete deterministic analysis pipeline."""

from fastapi import APIRouter

from app.schemas.analysis_schema import AnalysisRequest, AnalysisResponse
from app.services.analysis_service import analyze

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse)
def post_analyze(request: AnalysisRequest) -> AnalysisResponse:
    return analyze(request)
