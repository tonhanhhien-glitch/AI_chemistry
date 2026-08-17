"""Versioned aggregate contract for the complete analysis pipeline."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.properties.schema import NormalizedProperty
from app.schemas.bond_angle_schema import BondAnglesResult
from app.schemas.explanation_schema import ExplanationLevel, ExplanationResponse
from app.schemas.lewis_schema import LewisStructure
from app.schemas.molecule_schema import ExternalServiceStatus, ResolvedMolecule
from app.schemas.structure3d_schema import Structure3D
from app.schemas.vsepr_schema import VSEPRResult


class AnalysisRequest(BaseModel):
    """A raw chemical query, or an already-resolved identity.

    ``query`` is what the user typed -- a formula *or* a name. The backend decides
    which it is; the frontend no longer guesses from capitalisation. ``formula`` and
    ``molecule_id`` remain for already-resolved callers and for candidate re-submission.
    """

    query: str | None = Field(default=None, min_length=1, max_length=120)
    formula: str | None = Field(default=None, min_length=1, max_length=80)
    molecule_id: str | None = Field(default=None, min_length=1, max_length=80)
    pubchem_cid: int | None = Field(default=None, gt=0)
    include_explanation: bool = False
    explanation_level: ExplanationLevel = "intermediate"
    language: Literal["vi", "en"] = "vi"

    @model_validator(mode="after")
    def require_query(self) -> "AnalysisRequest":
        if not self.query and not self.formula and not self.molecule_id:
            raise ValueError("One of query, formula or molecule_id must be provided.")
        return self


class PropertyRequest(BaseModel):
    """Identity for the lazily-loaded property table."""

    formula: str | None = Field(default=None, min_length=1, max_length=80)
    molecule_id: str | None = Field(default=None, min_length=1, max_length=80)
    pubchem_cid: int | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def require_identity(self) -> "PropertyRequest":
        if not self.formula and not self.molecule_id:
            raise ValueError("Either formula or molecule_id must be provided.")
        return self


class AnalysisNotices(BaseModel):
    offline_capable: bool = True
    external_services_used: list[str] = Field(default_factory=list)
    warnings_vi: list[str] = Field(default_factory=list)
    warnings_en: list[str] = Field(default_factory=list)
    external_service_statuses: list[ExternalServiceStatus] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    schema_version: Literal["1.1"] = "1.1"
    molecule: ResolvedMolecule
    lewis: LewisStructure
    vsepr: VSEPRResult
    properties: list[NormalizedProperty]
    structure3d: Structure3D
    bond_angles: BondAnglesResult
    explanation: ExplanationResponse | None = None
    notices: AnalysisNotices
