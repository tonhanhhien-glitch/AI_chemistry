"""Persist anonymous study responses and export sanitized CSV."""

from app.schemas.feedback_schema import PersistenceResponse
from app.schemas.survey_schema import SurveyRequest
from app.services.persistence_service import anonymous_session_id, append_jsonl, export_csv, read_jsonl, timestamp_utc


def save_survey(request: SurveyRequest) -> PersistenceResponse:
    session_id = anonymous_session_id(request.session_id)
    append_jsonl("survey", {
        "session_id": session_id, "submitted_at": timestamp_utc(),
        "phase": request.phase, "answers": request.answers,
    })
    return PersistenceResponse(session_id=session_id, message_vi="Your anonymous answers have been saved.")


def export_study_csv(kind: str) -> str:
    if kind not in {"feedback", "survey"}:
        raise ValueError("kind must be feedback or survey")
    return export_csv(read_jsonl(kind))
