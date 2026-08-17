"""The educational fallback: an idealized AXnEm model, always labelled as such.

This provider is last in the resolution order and is the only one that may invent
a shape. Its evidence type is :attr:`GeometryEvidenceType.IDEAL_VSEPR`, so the UI
can say plainly that the student is looking at a teaching idealization rather than
a measurement or a conformer.
"""

from __future__ import annotations

import math
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from typing import Any

from app.geometry.providers.base import GeometryProviderResult, GeometryQuery, provider_status
from app.schemas.geometry_evidence_schema import (
    BondAngleObservation,
    BondLengthObservation,
    GeometryAtom,
    GeometryBond,
    GeometryCoordinate,
    GeometryEvidenceType,
    GeometryIdentity,
    GeometrySource,
    MolecularGeometryEvidence,
)
from app.schemas.molecule_schema import ExternalServiceState

_DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "geometry_templates_3d.json"

#: Uniform display bond length for idealized models; the shape is the teaching point.
IDEAL_BOND_LENGTH_ANGSTROM = 1.55

Vector = tuple[float, float, float]


@lru_cache(maxsize=1)
def templates() -> dict[str, Any]:
    from app.utils.file_loader import load_json

    return load_json(_DATA_FILE)["geometries"]


def normalize(vector: Vector) -> Vector:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 1e-12:
        raise ValueError("Cannot normalize a zero-length vector.")
    return (vector[0] / norm, vector[1] / norm, vector[2] / norm)


def reshape_ligands(ligands: list[Vector], target_deg: float) -> list[Vector] | None:
    """Open or close symmetry-equivalent ligand directions until every pair subtends ``target_deg``.

    The equivalent ligands of a template sit at one polar angle around a shared symmetry
    axis, so tilting them all by the same amount changes every inter-ligand angle together
    and keeps the geometry's symmetry. Returns ``None`` when the template has no such
    arrangement -- the ligands are centrosymmetric (tetrahedral, octahedral) or
    inequivalent (trigonal bipyramidal, seesaw) -- and when no tilt can reach the target.
    """

    if len(ligands) < 2:
        return None
    unit = [normalize(vector) for vector in ligands]
    total = tuple(sum(vector[axis] for vector in unit) for axis in range(3))
    if math.sqrt(sum(value * value for value in total)) <= 1e-8:
        return None
    axis = normalize(total)
    polar_cosines = [sum(value * reference for value, reference in zip(vector, axis, strict=True)) for vector in unit]
    if max(polar_cosines) - min(polar_cosines) > 1e-6:
        return None
    equatorial: list[Vector] = []
    for vector, polar_cosine in zip(unit, polar_cosines, strict=True):
        residual = tuple(value - polar_cosine * reference for value, reference in zip(vector, axis, strict=True))
        if math.sqrt(sum(value * value for value in residual)) <= 1e-8:
            return None
        equatorial.append(normalize(residual))
    pair_dots = [sum(left * right for left, right in zip(first, second, strict=True)) for first, second in combinations(equatorial, 2)]
    if max(pair_dots) - min(pair_dots) > 1e-6 or abs(1.0 - pair_dots[0]) <= 1e-9:
        return None
    # cos(pair) = cos²(polar) + pair_dot · sin²(polar); solve that for the polar angle.
    polar_cosine_squared = (math.cos(math.radians(target_deg)) - pair_dots[0]) / (1.0 - pair_dots[0])
    if not 0.0 <= polar_cosine_squared <= 1.0:
        return None
    polar_cosine = math.sqrt(polar_cosine_squared)
    polar_sine = math.sqrt(1.0 - polar_cosine_squared)
    return [
        tuple(polar_cosine * reference + polar_sine * value for reference, value in zip(axis, direction, strict=True))
        for direction in equatorial
    ]


class IdealVseprProvider:
    """Idealized AXnEm coordinates, optionally opened onto a molecule-specific angle.

    ``shape_target_deg`` lets a curated, molecule-specific teaching angle shape the
    drawing so the arc measured from the rendered coordinates agrees with the number
    shown beside it. The evidence type stays ``ideal_vsepr`` either way -- shaping a
    teaching model to a reference angle does not turn it into a measurement.
    """

    name = "ideal_vsepr"
    service = "Deterministic chemistry"

    def __init__(self, shape_target_deg: float | None = None, shape_source: str | None = None) -> None:
        self.shape_target_deg = shape_target_deg
        self.shape_source = shape_source

    def fetch(self, query: GeometryQuery) -> GeometryProviderResult:
        record = query.record or {}
        notation = record.get("ax_en")
        symbols = list(record.get("atom_symbols") or [])
        orders = list(record.get("bond_orders") or [])
        if not notation or notation not in templates() or len(symbols) < 2:
            return GeometryProviderResult(None, provider_status(
                self.service, ExternalServiceState.UNSUPPORTED_CHEMISTRY,
                message="No idealized template exists for this classification.",
            ))
        template = templates()[notation]
        ligands = [tuple(float(value) for value in vector) for vector in template["ligands"]]
        shaped = reshape_ligands(ligands, self.shape_target_deg) if self.shape_target_deg is not None else None
        directions = shaped or ligands
        if len(directions) != len(symbols) - 1:
            return GeometryProviderResult(None, provider_status(
                self.service, ExternalServiceState.UNSUPPORTED_CHEMISTRY,
                message="The idealized template does not match the ligand count.",
            ))

        points: list[Vector] = [(0.0, 0.0, 0.0)]
        points.extend(
            tuple(value * IDEAL_BOND_LENGTH_ANGSTROM for value in normalize(direction))
            for direction in directions
        )
        atom_ids = [f"a{index}" for index in range(len(symbols))]
        from app.geometry.fitter import angle_degrees, distance

        lengths = [
            BondLengthObservation(
                id=f"len-{index}", atom1_id=atom_ids[0], atom2_id=atom_ids[index + 1],
                value_angstrom=distance(points[0], points[index + 1]),
                label=f"{symbols[0]}–{symbols[index + 1]}",
            )
            for index in range(len(symbols) - 1)
        ]
        angles = []
        counter = 0
        for first, second in combinations(range(1, len(symbols)), 2):
            angles.append(BondAngleObservation(
                id=f"ang-{counter}", atom1_id=atom_ids[first], center_atom_id=atom_ids[0],
                atom2_id=atom_ids[second],
                value_deg=angle_degrees(points[first], points[0], points[second]),
                label=f"{symbols[first]}–{symbols[0]}–{symbols[second]}",
            ))
            counter += 1

        shaped_note = (
            f" Ligand directions were opened to the molecule-specific reference angle "
            f"{self.shape_target_deg:.2f}° ({self.shape_source})." if shaped and self.shape_target_deg else ""
        )
        evidence = MolecularGeometryEvidence(
            id=f"ideal-vsepr-{notation.casefold()}-{query.formula.casefold()}",
            identity=GeometryIdentity(
                formula=query.formula, charge=query.charge, atom_inventory=dict(query.atom_inventory),
                inchi=query.inchi, inchikey=query.inchikey, cas_rn=query.cas_rn,
                pubchem_cid=query.pubchem_cid, canonical_identity=query.canonical_identity,
                curated_molecule_id=query.curated_molecule_id,
            ),
            evidence_type=GeometryEvidenceType.IDEAL_VSEPR,
            atoms=[
                GeometryAtom(id=atom_ids[index], element=symbol, role="center" if index == 0 else "ligand")
                for index, symbol in enumerate(symbols)
            ],
            bonds=[
                GeometryBond(atom1_id=atom_ids[0], atom2_id=atom_ids[index + 1], order=int(order))
                for index, order in enumerate(orders)
            ],
            bond_lengths=lengths,
            bond_angles=angles,
            coordinates=[
                GeometryCoordinate(id=atom_ids[index], element=symbol, x=points[index][0], y=points[index][1], z=points[index][2])
                for index, symbol in enumerate(symbols)
            ],
            phase=None,
            point_group=None,
            source=GeometrySource(
                name="Idealized VSEPR model",
                reference=notation,
                comments=(
                    "Educational idealization built from the AXnEm electron-domain table. "
                    "Bond lengths are uniform and illustrative, not measured." + shaped_note
                ),
            ),
        )
        return GeometryProviderResult(evidence, provider_status(self.service, ExternalServiceState.SUCCESS))
