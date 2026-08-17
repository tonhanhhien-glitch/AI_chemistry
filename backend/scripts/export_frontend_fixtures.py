"""Regenerate the frontend test fixture from the live backend contract.

Run this after any schema change so the frontend tests exercise the shape the API
actually returns instead of a hand-maintained copy that can silently drift:

    cd backend && python scripts/export_frontend_fixtures.py
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

_TARGET = Path(__file__).resolve().parents[2] / "frontend" / "src" / "test" / "fixture.ts"

_TEMPLATE = '''import type {{ AnalysisResult }} from "../types/analysis";

// Generated from the live backend contract via backend/scripts/export_frontend_fixtures.py.
// Regenerate after any schema change so the frontend tests cannot drift from the API.

export const waterAnalysis: AnalysisResult = {water};

/** T-shaped ClF3: the multi-angle, experimental-geometry case. */
export const chlorineTrifluorideAnalysis: AnalysisResult = {clf3};
'''


def main() -> None:
    client = TestClient(app)
    water = client.post("/api/v1/analyze", json={"molecule_id": "h2o", "include_explanation": True}).json()
    clf3 = client.post("/api/v1/analyze", json={"molecule_id": "clf3"}).json()
    _TARGET.write_text(
        _TEMPLATE.format(
            water=json.dumps(water, ensure_ascii=False, indent=2),
            clf3=json.dumps(clf3, ensure_ascii=False, indent=2),
        ),
        encoding="utf-8",
    )
    print(f"wrote {_TARGET}")


if __name__ == "__main__":
    main()
