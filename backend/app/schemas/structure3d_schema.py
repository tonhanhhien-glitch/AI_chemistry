"""Typed 3D coordinates, provenance, bond angles, and electron-domain overlays."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


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
    CURATED_COORDINATES = "curated_coordinates"
    PUBCHEM_3D = "pubchem_3d"
    RDKIT_ETKDG = "rdkit_etkdg"
    IDEALIZED_VSEPR = "idealized_vsepr"


class ReferenceBondAngle(BaseModel):
    """The molecule-specific bond angle preferred over the generic AXnEm ideal angle.

    ``ideal_vsepr`` marks the fallback used when no molecule-specific value exists, so a
    consumer can tell "this molecule really bends to 104.5°" from "we only know the
    electron-domain ideal".
    """

    value_deg: float
    display_label: str
    category: Literal["measured", "curated_reference", "ideal_vsepr"]
    source: str
    is_approximate: bool = True


class BondAngleAnnotation(BaseModel):
    id: str
    atom1_id: str
    center_atom_id: str
    atom2_id: str
    value_deg: float | None
    display_label: str
    category: Literal["measured", "conformer", "ideal_vsepr", "curated_reference"]
    source: str
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
