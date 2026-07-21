"""Anonymous feedback submission models."""

from typing import Literal

from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    session_id: str | None = Field(default=None, max_length=80)
    molecule_id: str | None = Field(default=None, max_length=80)
    rating: int = Field(ge=1, le=5)
    category: Literal["clarity", "usefulness", "chemistry_error", "other"] = "clarity"
    comment: str | None = Field(default=None, max_length=1000)


class PersistenceResponse(BaseModel):
    accepted: bool = True
    session_id: str
    message_vi: str
