"""VSEPR output models."""

from pydantic import BaseModel, Field


class VSEPRResult(BaseModel):
    bonding_domains: int = Field(ge=0, le=6)
    lone_pair_domains: int = Field(ge=0, le=6)
    steric_number: int = Field(ge=2, le=6)
    ax_en: str
    electron_geometry: str
    electron_geometry_vi: str
    molecular_geometry: str
    molecular_geometry_vi: str
    ideal_angle: str
    distortion_note_vi: str | None = None
    distortion_note_en: str | None = None
    teaching_note_vi: str
    teaching_note_en: str
    pedagogical_hybridization: str | None = None
    hybridization_warning_vi: str | None = None
    hybridization_warning_en: str | None = None
