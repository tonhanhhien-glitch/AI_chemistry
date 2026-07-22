"""Anonymous survey submission and protected teacher CSV export."""

import secrets
from typing import Literal

from fastapi import APIRouter, Header, HTTPException, Query, Response

from app.core.config import settings
from app.schemas.feedback_schema import PersistenceResponse
from app.schemas.survey_schema import SurveyRequest
from app.services.survey_service import export_study_csv, save_survey

router = APIRouter()


@router.post("/survey", response_model=PersistenceResponse, status_code=201)
def post_survey(request: SurveyRequest) -> PersistenceResponse:
    return save_survey(request)


@router.get("/teacher/export")
def get_teacher_export(
    kind: Literal["feedback", "survey"] = Query("survey"),
    x_teacher_token: str = Header(default="", alias="X-Teacher-Token"),
) -> Response:
    configured = settings.TEACHER_EXPORT_TOKEN
    if not configured or not secrets.compare_digest(x_teacher_token, configured):
        raise HTTPException(status_code=403, detail={"code": "EXPORT_FORBIDDEN", "message": "The data-export token is invalid."})
    return Response(
        content=export_study_csv(kind), media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{kind}.csv"'},
    )
