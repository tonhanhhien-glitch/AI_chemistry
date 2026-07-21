"""Anonymous JSONL persistence and protected CSV export tests."""

import csv
import io
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

client = TestClient(app)


def test_feedback_survey_and_safe_export(tmp_path: Path) -> None:
    original_dir = settings.DATA_DIR
    original_token = settings.TEACHER_EXPORT_TOKEN
    settings.DATA_DIR = tmp_path
    settings.TEACHER_EXPORT_TOKEN = "teacher-secret"
    try:
        feedback = client.post("/api/v1/feedback", json={"rating": 4, "category": "other", "comment": "=HYPERLINK(\"bad\")"})
        assert feedback.status_code == 201
        session_id = feedback.json()["session_id"]
        UUID(session_id)
        survey = client.post("/api/v1/survey", json={"session_id": session_id, "consent": True, "phase": "pre", "answers": {"q1": 2}})
        assert survey.status_code == 201
        forbidden = client.get("/api/v1/teacher/export", params={"kind": "feedback"})
        assert forbidden.status_code == 403
        exported = client.get("/api/v1/teacher/export", params={"kind": "feedback"}, headers={"X-Teacher-Token": "teacher-secret"})
        assert exported.status_code == 200
        rows = list(csv.DictReader(io.StringIO(exported.text)))
        assert rows[0]["comment"].startswith("'=HYPERLINK")
        assert (tmp_path / "feedback.jsonl").exists()
        assert (tmp_path / "survey.jsonl").exists()
    finally:
        settings.DATA_DIR = original_dir
        settings.TEACHER_EXPORT_TOKEN = original_token


def test_survey_requires_consent(tmp_path: Path) -> None:
    original_dir = settings.DATA_DIR
    settings.DATA_DIR = tmp_path
    try:
        response = client.post("/api/v1/survey", json={"consent": False, "phase": "pre", "answers": {}})
        assert response.status_code == 422
        assert not (tmp_path / "survey.jsonl").exists()
    finally:
        settings.DATA_DIR = original_dir
