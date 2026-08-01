"""Provenance-aware molecular bond-angle evidence contract."""

from typing import Literal
from pydantic import BaseModel, Field


class BondAngleEvidence(BaseModel):
    id: str
    atom1_element: str
    center_element: str
    atom2_element: str
    atom1_id: str | None = None
    center_atom_id: str | None = None
    atom2_id: str | None = None
    value_deg: float | None
    display_label: str
    evidence_type: Literal["experimental", "curated_reference", "computed_conformer", "ideal_vsepr"]
    source_name: str
    source_url: str | None = None
    reference: str | None = None
    phase: str | None = None
    uncertainty_deg: float | None = None
    is_experimental: bool = False
    is_computed: bool = False
    is_approximate: bool = False
    equivalent_count: int = Field(default=1, ge=1)


class BondAnglesResult(BaseModel):
    preferred: list[BondAngleEvidence] = Field(default_factory=list)
    experimental: list[BondAngleEvidence] = Field(default_factory=list)
    coordinate_derived: list[BondAngleEvidence] = Field(default_factory=list)
    vsepr_prediction: list[BondAngleEvidence] = Field(default_factory=list)
    selection_reason: str
