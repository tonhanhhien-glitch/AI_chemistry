"""Request/response models for the Molecule Data admin page.

``MoleculeDraft`` mirrors the shape of an entry in ``curated_molecules.json``
(see that file for real examples) plus a handful of additional teaching and
provenance fields the admin UI exposes that the baseline file does not yet
use. ``extra="allow"`` keeps it forward-compatible with fields this module
does not need to know about, while the declared fields give the editor UI and
OpenAPI schema a concrete shape to build against.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.properties.schema import NormalizedProperty
from app.schemas.geometry_evidence_schema import MolecularGeometryEvidence


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class AdminSessionStatus(BaseModel):
    authenticated: bool
    username: str | None = None


class ExceptionFlags(BaseModel):
    electron_deficient: bool = False
    expanded_octet: bool = False
    odd_electron: bool = False


class ThreeDSource(BaseModel):
    kind: str = "idealized_vsepr_template"
    verified_reference: bool = False


class ResonanceStructureDraft(BaseModel):
    form_index: int
    bond_orders: list[int]
    lone_pairs: list[int]
    formal_charges: list[int]


class ReviewProvenance(BaseModel):
    """The Source & Review tab's own provenance block, separate from per-observation
    geometry/property sources -- this is the record-level "who curated this" trail."""

    source_name: str | None = None
    reference: str | None = None
    url: str | None = None
    evidence_type: str | None = None
    conditions: str | None = None
    retrieved_at: datetime | None = None


class MoleculeDraft(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str = Field(min_length=1, max_length=80)
    formula: str = Field(min_length=1, max_length=80)
    charge: int = 0
    name_vi: str = ""
    name_en: str = ""
    aliases: list[str] = Field(default_factory=list)

    cas_rn: str | None = None
    pubchem_cid: int | None = None
    smiles: str | None = None
    inchi: str | None = None
    inchikey: str | None = None

    atom_inventory: dict[str, int] = Field(default_factory=dict)
    atom_symbols: list[str] = Field(default_factory=list)
    central_atom: str = ""

    total_valence_electrons: int = 0
    bond_orders: list[int] = Field(default_factory=list)
    lone_pairs: list[int] = Field(default_factory=list)
    formal_charges: list[int] = Field(default_factory=list)
    resonance_forms: int = 1
    resonance_structures: list[ResonanceStructureDraft] = Field(default_factory=list)
    resonance_note_vi: str | None = None
    resonance_note_en: str | None = None
    exception_flags: ExceptionFlags = Field(default_factory=ExceptionFlags)

    bonding_domains: int = 0
    lone_pair_domains: int = 0
    steric_number: int = 0
    ax_en: str = ""
    electron_geometry: str = ""
    electron_geometry_vi: str = ""
    molecular_geometry: str = ""
    molecular_geometry_vi: str = ""
    ideal_angle: str = ""
    distortion_note_vi: str | None = None
    distortion_note_en: str | None = None
    hybridization: str | None = None
    hybridization_warning_vi: str | None = None
    hybridization_warning_en: str | None = None
    polarity_note_vi: str | None = None
    polarity_note_en: str | None = None

    teaching_note_vi: str | None = None
    teaching_note_en: str | None = None
    misconception_note_vi: str | None = None
    misconception_note_en: str | None = None
    structure_property_note_vi: str | None = None
    structure_property_note_en: str | None = None

    three_d_source: ThreeDSource = Field(default_factory=ThreeDSource)
    source: Literal["curated", "cache", "PubChem reference", "deterministic"] = "curated"
    confidence: Literal["high", "medium", "low"] = "medium"
    review_status: str = "draft"
    review_provenance: ReviewProvenance | None = None


class MoleculeAdminSaveRequest(BaseModel):
    molecule: MoleculeDraft
    experimental_geometry: MolecularGeometryEvidence | None = None
    properties: list[NormalizedProperty] = Field(default_factory=list)


class MoleculeAdminRecord(BaseModel):
    molecule: dict[str, Any]
    experimental_geometry: MolecularGeometryEvidence | None = None
    properties: list[NormalizedProperty] = Field(default_factory=list)
    has_override: bool = False
    is_admin_added: bool = False


class MoleculeAdminListItem(BaseModel):
    id: str
    formula: str
    charge: int
    name_vi: str
    name_en: str
    ax_en: str
    molecular_geometry: str
    molecular_geometry_vi: str
    review_status: str
    has_override: bool = False
    is_admin_added: bool = False


class MoleculeAdminListResponse(BaseModel):
    results: list[MoleculeAdminListItem]


class ValidationIssue(BaseModel):
    severity: Literal["error", "warning", "info"]
    field: str | None = None
    message_vi: str
    message_en: str


class ValidationReport(BaseModel):
    is_valid: bool
    errors: list[ValidationIssue] = Field(default_factory=list)
    warnings: list[ValidationIssue] = Field(default_factory=list)
    info: list[ValidationIssue] = Field(default_factory=list)


class MoleculeAdminSaveResponse(BaseModel):
    molecule: MoleculeAdminListItem
    validation: ValidationReport
    saved_at: datetime


class CompletenessReport(BaseModel):
    molecule_id: str
    missing_fields: list[str] = Field(default_factory=list)
    has_experimental_geometry: bool = False
    has_properties: bool = False
    review_status: str = ""
    completeness_percent: float = 0.0


class DraftGenerationRequest(BaseModel):
    formula: str = Field(min_length=1, max_length=80)
    charge: int = 0
    id: str | None = None
    name_vi: str | None = None
    name_en: str | None = None
