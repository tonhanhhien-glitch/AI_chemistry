"""Anonymous feedback route."""

from fastapi import APIRouter

from app.schemas.feedback_schema import FeedbackRequest, PersistenceResponse
from app.services.feedback_service import save_feedback

router = APIRouter()


@router.post("/feedback", response_model=PersistenceResponse, status_code=201)
def post_feedback(request: FeedbackRequest) -> PersistenceResponse:
    return save_feedback(request)
