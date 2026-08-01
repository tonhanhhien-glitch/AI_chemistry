"""Models for curated molecule identity and property provenance."""

from datetime import datetime
from enum import StrEnum
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


class ConnectivityAtom(BaseModel):
    id: str
    element: str


class ConnectivityBond(BaseModel):
    atom1_id: str
    atom2_id: str
    order: int = Field(ge=1, le=3)


class Connectivity(BaseModel):
    atoms: list[ConnectivityAtom]
    bonds: list[ConnectivityBond]
    central_atom_id: str


class ResolvedMolecule(MoleculeSummary):
    charge: int
    atom_inventory: dict[str, int]
    central_atom: str
    source: Literal["curated", "cache", "PubChem reference", "deterministic"] = "curated"
    confidence: Literal["high", "medium", "low"] = "high"
    pubchem_cid: int | None = None
    smiles: str | None = None
    canonical_identity: str | None = None
    inchi: str | None = None
    inchikey: str | None = None
    validation_status: str = "curated_verified"
    cache_timestamp: datetime | None = None
    connectivity: Connectivity | None = None


class ExternalServiceState(StrEnum):
    DISABLED = "disabled"
    CACHE_HIT = "cache_hit"
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    AMBIGUOUS = "ambiguous"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    TEMPORARY_FAILURE = "temporary_failure"
    INVALID_RESPONSE = "invalid_response"
    FORMULA_MISMATCH = "formula_mismatch"
    UNSUPPORTED_CHEMISTRY = "unsupported_chemistry"
    UNAVAILABLE = "unavailable"
    CONFORMER_UNAVAILABLE = "conformer_unavailable"


class ExternalServiceStatus(BaseModel):
    service: Literal["PubChem", "RDKit"]
    state: ExternalServiceState
    cache_hit: bool = False
    message: str | None = None


class PubChemCandidate(BaseModel):
    id: str
    cid: int
    formula: str
    charge: int
    name_vi: str
    name_en: str
    ax_en: str = "pending"
    molecular_geometry: str = "pending deterministic analysis"
    molecular_geometry_vi: str = "đang chờ phân tích tất định"
    review_status: str = "pubchem_identity_validated"
    canonical_smiles: str | None = None
    isomeric_smiles: str | None = None
    inchi: str | None = None
    inchikey: str | None = None
    molecular_weight: str | None = None
    title: str | None = None
    iupac_name: str | None = None
    covalent_unit_count: int | None = None
    source: str = "PubChem"
    validation_status: str = "formula_charge_inventory_validated"
    cache_timestamp: datetime | None = None


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
