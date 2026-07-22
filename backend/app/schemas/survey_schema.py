"""Minimal anonymous pre/post-test and Likert study models."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class SurveyRequest(BaseModel):
    session_id: str | None = Field(default=None, max_length=80)
    consent: bool
    phase: Literal["pre", "post", "likert"]
    answers: dict[str, int | str | bool] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_consent(self) -> "SurveyRequest":
        if not self.consent:
            raise ValueError("Consent to participate is required before submitting the survey.")
        if len(self.answers) > 30:
            raise ValueError("Too many answers.")
        return self
