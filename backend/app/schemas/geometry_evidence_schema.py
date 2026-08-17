"""General, provenance-aware molecular geometry evidence.

This module replaces the old "one molecule has one ``angle_pattern`` and one
``experimental_angle_deg``" assumption. A geometry is now a *collection of
observations* -- any number of bond lengths, inequivalent bond angles and
dihedrals -- attached to an explicit identity, phase, electronic state, point
group and source. Cartesian coordinates are optional, because real sources
(NIST CCCBDB in particular) often publish internal coordinates only; see
:mod:`app.geometry.fitter` for turning those constraints into coordinates.

Nothing here is molecule-specific: adding a species means adding data, never
code.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class GeometryEvidenceType(StrEnum):
    """How a geometry was obtained. Never blur these together in the UI."""

    EXPERIMENTAL = "experimental"
    """A measurement of the real substance (microwave, electron diffraction, ...)."""

    SOURCE_ANNOTATION = "source_annotation"
    """A value quoted by an external source without its own measurement provenance."""

    COMPUTED_CONFORMER = "computed_conformer"
    """A calculated 3D conformer (PubChem, RDKit). Not a measurement."""

    DETERMINISTIC_CALCULATION = "deterministic_calculation"
    """Derived by this application's own deterministic rules."""

    IDEAL_VSEPR = "ideal_vsepr"
    """An educational idealization from the AXnEm table."""


EXPERIMENTAL_EVIDENCE_TYPES = frozenset({GeometryEvidenceType.EXPERIMENTAL})


class GeometrySource(BaseModel):
    """Where a geometry came from, in enough detail for a student to check it."""

    name: str
    reference: str | None = None
    url: str | None = None
    comments: str | None = None
    retrieved_at: datetime | None = None


class GeometryObservationSource(BaseModel):
    """Provenance for a single geometric measurement or constraint."""

    source_name: str | None = None
    source_reference: str | None = None
    source_url: str | None = None
    comment: str | None = None
    retrieval_timestamp: datetime | None = None


class GeometryAtom(BaseModel):
    id: str
    element: str
    role: Literal["center", "ligand", "other"] = "other"


class GeometryBond(BaseModel):
    atom1_id: str
    atom2_id: str
    order: int = Field(default=1, ge=1, le=3)


class GeometryCoordinate(BaseModel):
    id: str
    element: str
    x: float
    y: float
    z: float


class BondLengthObservation(BaseModel):
    id: str
    atom1_id: str
    atom2_id: str
    value_angstrom: float = Field(gt=0.0)
    uncertainty_angstrom: float | None = Field(default=None, ge=0.0)
    equivalent_count: int = Field(default=1, ge=1)
    label: str | None = None
    source: GeometryObservationSource | None = None


class BondAngleObservation(BaseModel):
    id: str
    atom1_id: str
    center_atom_id: str
    atom2_id: str
    value_deg: float = Field(ge=0.0, le=180.0)
    uncertainty_deg: float | None = Field(default=None, ge=0.0)
    equivalent_count: int = Field(default=1, ge=1)
    label: str | None = None
    source: GeometryObservationSource | None = None


class DihedralObservation(BaseModel):
    id: str
    atom1_id: str
    atom2_id: str
    atom3_id: str
    atom4_id: str
    value_deg: float = Field(ge=-180.0, le=180.0)
    uncertainty_deg: float | None = Field(default=None, ge=0.0)
    equivalent_count: int = Field(default=1, ge=1)
    label: str | None = None
    source: GeometryObservationSource | None = None


class GeometryIdentity(BaseModel):
    """Strong identifiers, so a geometry is never matched on a bare formula by luck."""

    formula: str
    charge: int = 0
    atom_inventory: dict[str, int] = Field(default_factory=dict)
    inchi: str | None = None
    inchikey: str | None = None
    cas_rn: str | None = None
    pubchem_cid: int | None = None
    canonical_identity: str | None = None
    curated_molecule_id: str | None = None
    formula_identity_unambiguous: bool = False


class MolecularGeometryEvidence(BaseModel):
    """One source's complete statement about one species' geometry."""

    id: str
    identity: GeometryIdentity
    evidence_type: GeometryEvidenceType
    atoms: list[GeometryAtom] = Field(min_length=2)
    bonds: list[GeometryBond] = Field(default_factory=list)
    bond_lengths: list[BondLengthObservation] = Field(default_factory=list)
    bond_angles: list[BondAngleObservation] = Field(default_factory=list)
    dihedrals: list[DihedralObservation] = Field(default_factory=list)
    coordinates: list[GeometryCoordinate] | None = None
    units: Literal["angstrom"] = "angstrom"
    phase: str | None = None
    electronic_state: str | None = None
    conformation: str | None = None
    point_group: str | None = None
    source: GeometrySource

    @property
    def is_experimental(self) -> bool:
        return self.evidence_type in EXPERIMENTAL_EVIDENCE_TYPES

    @property
    def center_atom_id(self) -> str | None:
        return next((atom.id for atom in self.atoms if atom.role == "center"), None)

    def atom_elements(self) -> dict[str, str]:
        return {atom.id: atom.element for atom in self.atoms}

    def observation_count(self) -> int:
        return len(self.bond_lengths) + len(self.bond_angles) + len(self.dihedrals)

    @model_validator(mode="after")
    def _validate_references(self) -> "MolecularGeometryEvidence":
        ids = [atom.id for atom in self.atoms]
        if len(ids) != len(set(ids)):
            raise ValueError("Geometry atom ids must be unique.")
        known = set(ids)

        def check(*atom_ids: str) -> None:
            missing = [value for value in atom_ids if value not in known]
            if missing:
                raise ValueError(f"Geometry observation references unknown atom ids: {missing}.")

        for bond in self.bonds:
            check(bond.atom1_id, bond.atom2_id)
        for length in self.bond_lengths:
            check(length.atom1_id, length.atom2_id)
            if length.atom1_id == length.atom2_id:
                raise ValueError("A bond length needs two distinct atoms.")
        for angle in self.bond_angles:
            check(angle.atom1_id, angle.center_atom_id, angle.atom2_id)
            if len({angle.atom1_id, angle.center_atom_id, angle.atom2_id}) != 3:
                raise ValueError("A bond angle needs three distinct atoms.")
        for dihedral in self.dihedrals:
            check(dihedral.atom1_id, dihedral.atom2_id, dihedral.atom3_id, dihedral.atom4_id)
            if len({dihedral.atom1_id, dihedral.atom2_id, dihedral.atom3_id, dihedral.atom4_id}) != 4:
                raise ValueError("A dihedral needs four distinct atoms.")
        if self.coordinates is not None:
            coordinate_ids = [item.id for item in self.coordinates]
            if sorted(coordinate_ids) != sorted(ids):
                raise ValueError("Geometry coordinates must cover exactly the declared atoms.")
            elements = self.atom_elements()
            for item in self.coordinates:
                if elements[item.id] != item.element:
                    raise ValueError("Coordinate element does not match the declared atom element.")
        if self.identity.atom_inventory:
            inventory: dict[str, int] = {}
            for atom in self.atoms:
                inventory[atom.element] = inventory.get(atom.element, 0) + 1
            if inventory != self.identity.atom_inventory:
                raise ValueError("Geometry atoms do not match the declared atom inventory.")
        if sum(1 for atom in self.atoms if atom.role == "center") > 1:
            raise ValueError("A geometry record may declare at most one central atom.")
        return self


class GeometryLengthSummary(BaseModel):
    """Symmetry-grouped bond lengths for display."""

    label: str
    value_angstrom: float
    uncertainty_angstrom: float | None = None
    equivalent_count: int = Field(default=1, ge=1)


class GeometryEvidenceSummary(BaseModel):
    """Flattened provenance block attached to whatever geometry was actually rendered.

    The student-facing rule is that no geometry appears without saying where it came
    from, so this travels with every structure -- experimental, computed or ideal.
    """

    id: str
    evidence_type: GeometryEvidenceType
    provider: str
    source_name: str
    source_reference: str | None = None
    source_url: str | None = None
    source_comments: str | None = None
    retrieved_at: datetime | None = None
    phase: str | None = None
    electronic_state: str | None = None
    conformation: str | None = None
    point_group: str | None = None
    units: Literal["angstrom"] = "angstrom"
    bond_lengths: list[GeometryLengthSummary] = Field(default_factory=list)
    bond_length_count: int = 0
    bond_angle_count: int = 0
    dihedral_count: int = 0
    coordinates_are_fitted: bool = False
    max_length_deviation_angstrom: float | None = None
    max_angle_deviation_deg: float | None = None
    is_experimental: bool = False
    is_computed: bool = False
    is_ideal: bool = False
    provenance_label_vi: str
    provenance_label_en: str
