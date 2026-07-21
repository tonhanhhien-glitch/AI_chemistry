"""Frontend-ready Lewis structure models."""

from typing import Literal

from pydantic import BaseModel, Field


class LewisAtom(BaseModel):
    id: str
    element: str
    x: float
    y: float
    lone_pairs: int = Field(ge=0)
    formal_charge: int = 0


class LewisBond(BaseModel):
    id: str
    atom1_id: str
    atom2_id: str
    order: Literal[1, 2, 3]


class OctetExceptionFlags(BaseModel):
    electron_deficient: bool = False
    expanded_octet: bool = False
    odd_electron: bool = False
    note_vi: str | None = None


class LewisStructure(BaseModel):
    atoms: list[LewisAtom]
    bonds: list[LewisBond]
    central_atom_id: str
    total_valence_electrons: int = Field(ge=0)
    resonance_forms: int = Field(default=1, ge=1)
    resonance_note_vi: str | None = None
    exception_flags: OctetExceptionFlags
    source: Literal["curated", "validated_connectivity"]
    confidence: Literal["high", "medium", "low"]
    review_status: str
