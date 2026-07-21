"""Models for immutable-facts AI explanations and deterministic fallbacks."""

from typing import Literal

from pydantic import BaseModel, Field

ExplanationLevel = Literal["basic", "intermediate", "advanced"]
ExplanationLanguage = Literal["vi", "en"]


class ExplanationSections(BaseModel):
    lewis: str
    ax_en: str
    electron_geometry: str
    molecular_geometry: str
    structure_property: str
    learning_tip: str
    disclaimer: str


class ExplanationRequest(BaseModel):
    molecule_id: str = Field(min_length=1, max_length=80)
    level: ExplanationLevel = "intermediate"
    language: ExplanationLanguage = "vi"


class ExplanationResponse(BaseModel):
    formula: str
    level: ExplanationLevel
    language: ExplanationLanguage
    sections: ExplanationSections
    source: Literal["claude", "deterministic_fallback"]
    fallback_reason: str | None = None
    prompt_version: str = "1.0"
    facts_validated: bool = True
