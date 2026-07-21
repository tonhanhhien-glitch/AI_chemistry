"""Versioned aggregate contract for the complete analysis pipeline."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.explanation_schema import ExplanationLevel, ExplanationResponse
from app.schemas.lewis_schema import LewisStructure
from app.schemas.molecule_schema import PropertyItem, ResolvedMolecule
from app.schemas.structure3d_schema import Structure3D
from app.schemas.vsepr_schema import VSEPRResult


class AnalysisRequest(BaseModel):
    formula: str | None = Field(default=None, min_length=1, max_length=80)
    molecule_id: str | None = Field(default=None, min_length=1, max_length=80)
    include_explanation: bool = False
    explanation_level: ExplanationLevel = "intermediate"
    language: Literal["vi", "en"] = "vi"

    @model_validator(mode="after")
    def require_query(self) -> "AnalysisRequest":
        if not self.formula and not self.molecule_id:
            raise ValueError("Cần cung cấp formula hoặc molecule_id.")
        return self


class AnalysisNotices(BaseModel):
    offline_capable: bool = True
    external_services_used: list[str] = Field(default_factory=list)
    warnings_vi: list[str] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    molecule: ResolvedMolecule
    lewis: LewisStructure
    vsepr: VSEPRResult
    properties: list[PropertyItem]
    structure3d: Structure3D
    explanation: ExplanationResponse | None = None
    notices: AnalysisNotices
