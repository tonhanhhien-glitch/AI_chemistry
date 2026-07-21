"""Models for curated molecule identity and property provenance."""

from typing import Literal

from pydantic import BaseModel, Field


class MoleculeSummary(BaseModel):
    id: str
    formula: str
    name_vi: str
    name_en: str
    ax_en: str
    molecular_geometry: str
    molecular_geometry_vi: str
    review_status: str


class ResolvedMolecule(MoleculeSummary):
    charge: int
    atom_inventory: dict[str, int]
    central_atom: str
    source: Literal["curated", "cache", "PubChem reference"] = "curated"
    confidence: Literal["high", "medium", "low"] = "high"
    pubchem_cid: int | None = None
    smiles: str | None = None


class PropertyItem(BaseModel):
    key: str
    label_vi: str
    value: str | float | int
    unit: str | None = None
    provenance: Literal["curated", "computed", "PubChem reference"]
    verified_teaching_fact: bool = False
    note_vi: str | None = None


class MoleculeSearchResponse(BaseModel):
    query: str
    results: list[MoleculeSummary] = Field(default_factory=list)
