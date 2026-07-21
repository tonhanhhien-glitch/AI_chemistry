"""Coordinate-schema output consumed by the 3D viewer."""

from typing import Literal

from pydantic import BaseModel


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


class Structure3D(BaseModel):
    format: Literal["coordinates", "molblock", "sdf", "pdb"] = "coordinates"
    atoms: list[Structure3DAtom]
    bonds: list[Structure3DBond]
    data: str | None = None
    source: str
    is_illustrative: bool
    warning_vi: str | None = None
