"""Models for immutable-facts AI explanations and deterministic fallbacks."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

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
    molecule_id: str | None = Field(default=None, min_length=1, max_length=80)
    formula: str | None = Field(default=None, min_length=1, max_length=80)
    pubchem_cid: int | None = Field(default=None, gt=0)
    level: ExplanationLevel = "intermediate"
    language: ExplanationLanguage = "vi"

    @model_validator(mode="after")
    def require_identity(self) -> "ExplanationRequest":
        if not self.molecule_id and not self.formula:
            raise ValueError("Either molecule_id or formula must be provided.")
        return self


class ExplanationResponse(BaseModel):
    formula: str
    level: ExplanationLevel
    language: ExplanationLanguage
    sections: ExplanationSections
    source: Literal["openrouter", "openai", "deterministic_fallback"]
    fallback_reason: str | None = None
    prompt_version: str = "1.0"
    facts_validated: bool = True
