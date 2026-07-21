"""Persist only anonymous, minimal feedback fields."""

from app.schemas.feedback_schema import FeedbackRequest, PersistenceResponse
from app.services.persistence_service import anonymous_session_id, append_jsonl, timestamp_utc


def save_feedback(request: FeedbackRequest) -> PersistenceResponse:
    session_id = anonymous_session_id(request.session_id)
    append_jsonl("feedback", {
        "session_id": session_id, "submitted_at": timestamp_utc(),
        "molecule_id": request.molecule_id, "rating": request.rating,
        "category": request.category, "comment": request.comment,
    })
    return PersistenceResponse(session_id=session_id, message_vi="Cảm ơn bạn. Phản hồi ẩn danh đã được lưu.")
