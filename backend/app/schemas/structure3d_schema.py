"""Typed 3D coordinates, provenance, bond angles, and electron-domain overlays."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.geometry_evidence_schema import GeometryEvidenceSummary, GeometryEvidenceType


class Structure3DAtom(BaseModel):
    id: str
    element: str
    x: float
    y: float
    z: float


class Structure3DBond(BaseModel):
    atom1_id: str
    atom2_id: str
    order: int


class Vector3D(BaseModel):
    x: float
    y: float
    z: float


class StructureSource(StrEnum):
    EXPERIMENTAL_GEOMETRY = "experimental_geometry"
    CURATED_COORDINATES = "curated_coordinates"
    PUBCHEM_3D = "pubchem_3d"
    RDKIT_ETKDG = "rdkit_etkdg"
    IDEALIZED_VSEPR = "idealized_vsepr"


class ReferenceBondAngle(BaseModel):
    """Deprecated single-angle summary kept only for backwards compatibility.

    Geometries with several inequivalent angles cannot be described by one number,
    which is exactly why geometry is now a collection of observations. No chemistry
    logic reads this field; consumers should use ``angle_annotations`` (measured from
    the rendered coordinates) or the ``bond_angles`` evidence bundle instead.
    """

    value_deg: float
    display_label: str
    category: Literal["measured", "curated_reference", "ideal_vsepr"]
    source: str
    is_approximate: bool = True
    deprecated: bool = True


class BondAngleAnnotation(BaseModel):
    """One angle of the structure actually on screen.

    ``coordinate_value_deg`` is always measured from the rendered coordinates.
    ``source_value_deg`` is the value the evidence source published, present only when
    a source observation matched this atom triple and the rendered coordinates
    reproduce it within tolerance. ``value_deg`` is the number to display: the source
    value when one is verified, otherwise the coordinate measurement. That keeps the
    displayed number tied to the drawn geometry without rounding a measurement away.
    """

    id: str
    atom1_id: str
    center_atom_id: str
    atom2_id: str
    value_deg: float | None
    coordinate_value_deg: float | None = None
    source_value_deg: float | None = None
    deviation_deg: float | None = None
    uncertainty_deg: float | None = None
    display_label: str
    category: Literal["measured", "conformer", "ideal_vsepr", "curated_reference"]
    evidence_type: GeometryEvidenceType = GeometryEvidenceType.IDEAL_VSEPR
    source: str
    source_reference: str | None = None
    source_url: str | None = None
    phase: str | None = None
    is_approximate: bool = False
    equivalent_count: int = Field(default=1, ge=1)
    note_vi: str | None = None
    note_en: str | None = None


class ElectronDomain3D(BaseModel):
    id: str
    center_atom_id: str
    kind: Literal["bonding", "lone_pair"]
    occupancy: int = 2
    direction: Vector3D
    position: Vector3D
    source: str
    is_illustrative: bool = True
    label_vi: str
    label_en: str


class Structure3D(BaseModel):
    format: Literal["coordinates", "molblock", "sdf", "pdb"] = "coordinates"
    atoms: list[Structure3DAtom]
    bonds: list[Structure3DBond]
    data: str | None = None
    source: StructureSource
    source_label: str
    evidence_type: GeometryEvidenceType = GeometryEvidenceType.IDEAL_VSEPR
    geometry_evidence: GeometryEvidenceSummary | None = None
    is_illustrative: bool
    is_computed: bool = False
    is_experimental: bool = False
    pubchem_cid: int | None = None
    central_atom_id: str | None = None
    reference_bond_angle: ReferenceBondAngle | None = None
    angle_annotations: list[BondAngleAnnotation] = Field(default_factory=list)
    electron_domains: list[ElectronDomain3D] = Field(default_factory=list)
    warning_vi: str | None = None
    warning_en: str | None = None
