"""Validated local snapshot of explicitly sourced experimental geometries."""

from collections import Counter
from functools import lru_cache
import math
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.services.formula_parser import parse_formula
from app.utils.file_loader import load_json

_DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "experimental_geometries.json"


class ExperimentalCoordinate(BaseModel):
    id: str
    element: str
    x: float
    y: float
    z: float


class AnglePattern(BaseModel):
    atom1_element: str
    center_element: str
    atom2_element: str


class ExperimentalGeometryRecord(BaseModel):
    id: str
    curated_molecule_id: str | None = None
    formula: str
    charge: int
    atom_inventory: dict[str, int]
    formula_identity_unambiguous: bool = False
    cas_rn: str
    pubchem_cid: int
    inchi: str
    inchikey: str
    angle_pattern: AnglePattern
    experimental_angle_deg: float
    phase: str
    point_group_conformation: str
    reference_label: str
    source_name: str
    source_url: str
    units: str
    retrieval_date: str
    coordinates: list[ExperimentalCoordinate] = Field(min_length=3)

    @model_validator(mode="after")
    def validate_identity_and_coordinates(self) -> "ExperimentalGeometryRecord":
        parsed = parse_formula(self.formula)
        if parsed.charge != self.charge or parsed.atoms != self.atom_inventory:
            raise ValueError("Experimental formula, charge, and inventory are inconsistent.")
        if Counter(atom.element for atom in self.coordinates) != Counter(self.atom_inventory):
            raise ValueError("Experimental coordinates do not match the atom inventory.")
        ids = [atom.id for atom in self.coordinates]
        if len(ids) != len(set(ids)) or self.units != "angstrom":
            raise ValueError("Experimental coordinate IDs must be unique and units must be angstrom.")
        centers = [atom for atom in self.coordinates if atom.element == self.angle_pattern.center_element]
        outer1 = [atom for atom in self.coordinates if atom.element == self.angle_pattern.atom1_element]
        outer2 = [atom for atom in self.coordinates if atom.element == self.angle_pattern.atom2_element]
        if len(centers) != 1 or not outer1 or not outer2:
            raise ValueError("Experimental angle pattern is inconsistent with the coordinates.")
        center = centers[0]
        if self.angle_pattern.atom1_element == self.angle_pattern.atom2_element:
            if len(outer1) < 2:
                raise ValueError("Experimental angle pattern requires two matching outer atoms.")
            atom1, atom2 = outer1[:2]
        else:
            atom1, atom2 = outer1[0], outer2[0]
        vector1 = (atom1.x - center.x, atom1.y - center.y, atom1.z - center.z)
        vector2 = (atom2.x - center.x, atom2.y - center.y, atom2.z - center.z)
        norm = math.sqrt(sum(value * value for value in vector1) * sum(value * value for value in vector2))
        if norm == 0:
            raise ValueError("Experimental angle contains a zero-length bond vector.")
        cosine = max(-1.0, min(1.0, sum(a * b for a, b in zip(vector1, vector2)) / norm))
        coordinate_angle = math.degrees(math.acos(cosine))
        if abs(coordinate_angle - self.experimental_angle_deg) > 0.05:
            raise ValueError("Experimental angle does not match the stored coordinates.")
        return self


@lru_cache(maxsize=1)
def experimental_records() -> tuple[ExperimentalGeometryRecord, ...]:
    payload = load_json(_DATA_FILE)
    records = tuple(ExperimentalGeometryRecord.model_validate(item) for item in payload.get("records", []))
    if not records:
        raise ValueError("experimental_geometries.json contains no records")
    return records


def match_experimental_geometry(identity: dict[str, Any]) -> ExperimentalGeometryRecord | None:
    charge = int(identity["charge"])
    inchikey = identity.get("inchikey")
    if inchikey:
        matches = [item for item in experimental_records() if item.inchikey == inchikey and item.charge == charge]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            return None
    molecule_id = identity.get("id")
    if molecule_id:
        matches = [item for item in experimental_records() if item.curated_molecule_id == molecule_id and item.charge == charge]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            return None
    matches = [item for item in experimental_records() if item.formula == identity.get("formula") and item.charge == charge and item.atom_inventory == identity.get("atom_inventory") and item.formula_identity_unambiguous]
    return matches[0] if len(matches) == 1 else None
