"""Resolve 3D structures and derive coordinate-faithful educational overlays."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from typing import Any

from app.schemas.molecule_schema import ExternalServiceState, ExternalServiceStatus
from app.schemas.structure3d_schema import (
    BondAngleAnnotation,
    ElectronDomain3D,
    ReferenceBondAngle,
    Structure3D,
    Structure3DAtom,
    Structure3DBond,
    StructureSource,
    Vector3D,
)
from app.services.experimental_geometry_service import ExperimentalGeometryRecord, match_experimental_geometry
from app.services.pubchem_service import fetch_pubchem_3d
from app.services.rdkit_service import generate_rdkit_result
from app.services.reference_angle_service import resolve_reference_angle
from app.utils.file_loader import load_json

_DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "geometry_templates_3d.json"


@dataclass(frozen=True, slots=True)
class Structure3DResult:
    structure: Structure3D
    statuses: tuple[ExternalServiceStatus, ...] = ()


@lru_cache(maxsize=1)
def _templates() -> dict[str, Any]:
    return load_json(_DATA_FILE)["geometries"]


def _xyz(atom: Structure3DAtom) -> tuple[float, float, float]:
    return atom.x, atom.y, atom.z


def calculate_angle(
    atom_a: Structure3DAtom,
    central_atom: Structure3DAtom,
    atom_b: Structure3DAtom,
) -> float:
    """Calculate A-center-B in degrees without display-time rounding."""

    vector1 = tuple(a - c for a, c in zip(_xyz(atom_a), _xyz(central_atom), strict=True))
    vector2 = tuple(b - c for b, c in zip(_xyz(atom_b), _xyz(central_atom), strict=True))
    norm1 = math.sqrt(sum(value * value for value in vector1))
    norm2 = math.sqrt(sum(value * value for value in vector2))
    if norm1 <= 1e-12 or norm2 <= 1e-12:
        raise ValueError("Bond-angle vectors must have non-zero length.")
    cosine = sum(left * right for left, right in zip(vector1, vector2, strict=True)) / (norm1 * norm2)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def _normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 1e-12:
        raise ValueError("Cannot normalize a zero-length vector.")
    return tuple(value / norm for value in vector)


def _reshape_ligands(
    ligands: list[tuple[float, float, float]],
    target_deg: float,
) -> list[tuple[float, float, float]] | None:
    """Open or close symmetry-equivalent ligand directions until every pair subtends ``target_deg``.

    The equivalent ligands of a template sit at one polar angle around a shared symmetry axis,
    so tilting them all by the same amount changes every inter-ligand angle together and keeps
    the geometry's symmetry. Returns ``None`` when the template has no such arrangement -- the
    ligands are centrosymmetric (tetrahedral, octahedral) or inequivalent (trigonal
    bipyramidal, seesaw) -- and when no tilt can reach the target.
    """

    if len(ligands) < 2:
        return None
    unit = [_normalize(vector) for vector in ligands]
    total = tuple(sum(vector[axis] for vector in unit) for axis in range(3))
    if math.sqrt(sum(value * value for value in total)) <= 1e-8:
        return None
    axis = _normalize(total)
    polar_cosines = [sum(value * reference for value, reference in zip(vector, axis, strict=True)) for vector in unit]
    if max(polar_cosines) - min(polar_cosines) > 1e-6:
        return None
    equatorial: list[tuple[float, float, float]] = []
    for vector, polar_cosine in zip(unit, polar_cosines, strict=True):
        residual = tuple(value - polar_cosine * reference for value, reference in zip(vector, axis, strict=True))
        if math.sqrt(sum(value * value for value in residual)) <= 1e-8:
            return None
        equatorial.append(_normalize(residual))
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


def _parse_v2000(data: str, record: dict[str, Any]) -> tuple[list[Structure3DAtom], list[Structure3DBond], str] | None:
    lines = data.splitlines()
    counts_index = next((index for index, line in enumerate(lines) if "V2000" in line), None)
    if counts_index is None:
        return None
    try:
        counts = lines[counts_index].split()
        atom_count, bond_count = int(counts[0]), int(counts[1])
        atom_lines = lines[counts_index + 1 : counts_index + 1 + atom_count]
        bond_lines = lines[counts_index + 1 + atom_count : counts_index + 1 + atom_count + bond_count]
        atoms = []
        for index, line in enumerate(atom_lines):
            parts = line.split()
            atoms.append(Structure3DAtom(id=f"a{index}", x=float(parts[0]), y=float(parts[1]), z=float(parts[2]), element=parts[3]))
        bonds = []
        for line in bond_lines:
            parts = line.split()
            bonds.append(Structure3DBond(atom1_id=f"a{int(parts[0]) - 1}", atom2_id=f"a{int(parts[1]) - 1}", order=int(parts[2])))
    except (IndexError, TypeError, ValueError):
        return None
    if Counter(atom.element for atom in atoms) != Counter(record["atom_inventory"]):
        return None
    degrees = Counter()
    for bond in bonds:
        degrees[bond.atom1_id] += 1
        degrees[bond.atom2_id] += 1
    possible = [atom for atom in atoms if atom.element == record["central_atom"]]
    if not possible:
        return None
    center = max(possible, key=lambda atom: degrees[atom.id])
    if degrees[center.id] != record["bonding_domains"]:
        return None
    return atoms, bonds, center.id


def _angle_annotations(
    atoms: list[Structure3DAtom],
    bonds: list[Structure3DBond],
    center_id: str,
    category: str,
    source: str,
    *,
    is_approximate: bool | None = None,
) -> list[BondAngleAnnotation]:
    by_id = {atom.id: atom for atom in atoms}
    neighbors = []
    for bond in bonds:
        if bond.atom1_id == center_id:
            neighbors.append(bond.atom2_id)
        elif bond.atom2_id == center_id:
            neighbors.append(bond.atom1_id)
    measured: list[tuple[float, str, str]] = []
    for atom1_id, atom2_id in combinations(neighbors, 2):
        value = calculate_angle(by_id[atom1_id], by_id[center_id], by_id[atom2_id])
        measured.append((value, atom1_id, atom2_id))
    representatives: list[tuple[float, str, str, int]] = []
    for value, atom1_id, atom2_id in sorted(measured):
        match_index = next((index for index, existing in enumerate(representatives) if abs(value - existing[0]) < 0.01), None)
        if match_index is None:
            representatives.append((value, atom1_id, atom2_id, 1))
        else:
            existing = representatives[match_index]
            representatives[match_index] = (*existing[:3], existing[3] + 1)
    return [
        BondAngleAnnotation(
            id=f"angle-{index}",
            atom1_id=atom1_id,
            center_atom_id=center_id,
            atom2_id=atom2_id,
            value_deg=value,
            display_label=f"{value:.1f}°",
            category=category,
            source=source,
            is_approximate=category == "ideal_vsepr" if is_approximate is None else is_approximate,
            equivalent_count=equivalent_count,
            note_vi="Góc được tính trực tiếp từ tọa độ đang hiển thị.",
            note_en="Angle calculated directly from the rendered coordinates.",
        )
        for index, (value, atom1_id, atom2_id, equivalent_count) in enumerate(representatives)
    ]


def _electron_domains(
    atoms: list[Structure3DAtom],
    bonds: list[Structure3DBond],
    center_id: str,
    record: dict[str, Any],
    source: str,
    template_lone_pairs: list[list[float]] | None = None,
) -> list[ElectronDomain3D]:
    by_id = {atom.id: atom for atom in atoms}
    center = by_id[center_id]
    domains: list[ElectronDomain3D] = []
    bond_directions: list[tuple[float, float, float]] = []
    for bond in bonds:
        neighbor_id = bond.atom2_id if bond.atom1_id == center_id else bond.atom1_id if bond.atom2_id == center_id else None
        if neighbor_id is None:
            continue
        neighbor = by_id[neighbor_id]
        direction = _normalize((neighbor.x - center.x, neighbor.y - center.y, neighbor.z - center.z))
        bond_directions.append(direction)
        domains.append(ElectronDomain3D(
            id=f"bond-domain-{len(domains)}", center_atom_id=center_id, kind="bonding",
            direction=Vector3D(x=direction[0], y=direction[1], z=direction[2]),
            position=Vector3D(x=(center.x + neighbor.x) / 2, y=(center.y + neighbor.y) / 2, z=(center.z + neighbor.z) / 2),
            source=source, label_vi="Miền electron liên kết", label_en="Bonding electron domain",
        ))
    lone_pair_count = int(record["lone_pair_domains"])
    directions: list[tuple[float, float, float]] = []
    summed = tuple(sum(vector[axis] for vector in bond_directions) for axis in range(3))
    if lone_pair_count == 1 and math.sqrt(sum(value * value for value in summed)) > 1e-8:
        directions = [_normalize(tuple(-value for value in summed))]
    else:
        raw = template_lone_pairs if template_lone_pairs is not None else _templates()[record["ax_en"]]["lone_pairs"]
        directions = [_normalize(tuple(float(value) for value in vector)) for vector in raw[:lone_pair_count]]
    for index, direction in enumerate(directions):
        distance = 1.15
        domains.append(ElectronDomain3D(
            id=f"lone-pair-{index}", center_atom_id=center_id, kind="lone_pair",
            direction=Vector3D(x=direction[0], y=direction[1], z=direction[2]),
            position=Vector3D(x=center.x + distance * direction[0], y=center.y + distance * direction[1], z=center.z + distance * direction[2]),
            source="illustrative VSEPR orientation", is_illustrative=True,
            label_vi="Miền cặp electron tự do (minh họa)",
            label_en="Lone-pair electron domain (illustrative)",
        ))
    return domains


def _from_block(record: dict[str, Any], data: str, *, reference: ReferenceBondAngle | None, source: StructureSource, source_label: str, data_format: str, pubchem_cid: int | None = None) -> Structure3D | None:
    parsed = _parse_v2000(data, record)
    if parsed is None:
        return None
    atoms, bonds, center_id = parsed
    category = "conformer"
    warning_vi = "Tọa độ cấu dạng là dữ liệu tính toán; các miền cặp electron tự do chỉ là lớp minh họa VSEPR."
    warning_en = "Conformer coordinates are computed; lone-pair domains are only an illustrative VSEPR overlay."
    return Structure3D(
        format=data_format, atoms=atoms, bonds=bonds, data=data,
        source=source, source_label=source_label, is_illustrative=False,
        is_computed=True, is_experimental=False, pubchem_cid=pubchem_cid,
        central_atom_id=center_id, reference_bond_angle=reference,
        angle_annotations=_angle_annotations(atoms, bonds, center_id, category, source_label),
        electron_domains=_electron_domains(atoms, bonds, center_id, record, source_label),
        warning_vi=warning_vi, warning_en=warning_en,
    )


def _experimental(record: dict[str, Any], experimental: ExperimentalGeometryRecord, reference: ReferenceBondAngle | None) -> Structure3D:
    atoms = [Structure3DAtom(**atom.model_dump()) for atom in experimental.coordinates]
    center_id = next(atom.id for atom in atoms if atom.element == record["central_atom"])
    ligand_ids = [atom.id for atom in atoms if atom.id != center_id]
    bonds = [Structure3DBond(atom1_id=center_id, atom2_id=atom_id, order=order) for atom_id, order in zip(ligand_ids, record["bond_orders"], strict=True)]
    label = "NIST CCCBDB experimental gas-phase geometry"
    annotations = _angle_annotations(atoms, bonds, center_id, "measured", label)
    return Structure3D(
        atoms=atoms, bonds=bonds, source=StructureSource.CURATED_COORDINATES, source_label=label,
        is_illustrative=False, is_computed=False, is_experimental=True, pubchem_cid=experimental.pubchem_cid,
        central_atom_id=center_id, reference_bond_angle=reference, angle_annotations=annotations,
        electron_domains=_electron_domains(atoms, bonds, center_id, record, label),
        warning_vi="Tọa độ nguyên tử là hình học pha khí thực nghiệm từ NIST CCCBDB; các miền cặp electron tự do vẫn chỉ là minh họa VSEPR.",
        warning_en="Atomic coordinates are an experimental gas-phase geometry from NIST CCCBDB; lone-pair domains remain illustrative VSEPR overlays.",
    )


def _idealized(record: dict[str, Any], reference: ReferenceBondAngle | None) -> Structure3D:
    """Build the fallback model, shaped to the molecule-specific reference angle where one exists.

    The generic AXnEm template only knows the electron-domain ideal, so water would come out at
    the tetrahedral 109.5°. Bending the ligands onto the reference angle first keeps the drawn
    geometry, the arc measured from it, and the summary's preferred angle in agreement.
    """

    template = _templates()[record["ax_en"]]
    ligands = [tuple(float(value) for value in vector) for vector in template["ligands"]]
    shaped = _reshape_ligands(ligands, reference.value_deg) if reference is not None else None
    is_molecule_specific = shaped is not None and reference is not None and reference.category != "ideal_vsepr"
    coordinates = [(0.0, 0.0, 0.0), *(shaped or ligands)]
    scale = 1.55
    atoms = [
        Structure3DAtom(id=f"a{index}", element=symbol, x=coordinates[index][0] * scale, y=coordinates[index][1] * scale, z=coordinates[index][2] * scale)
        for index, symbol in enumerate(record["atom_symbols"])
    ]
    bonds = [Structure3DBond(atom1_id="a0", atom2_id=f"a{index + 1}", order=order) for index, order in enumerate(record["bond_orders"])]
    label = f"Idealized VSEPR model at the {reference.display_label} reference angle" if is_molecule_specific and reference else "Idealized VSEPR model"
    category = reference.category if is_molecule_specific and reference else "ideal_vsepr"
    return Structure3D(
        atoms=atoms, bonds=bonds, source=StructureSource.IDEALIZED_VSEPR,
        source_label=label, is_illustrative=True, is_computed=False,
        is_experimental=False, central_atom_id="a0", reference_bond_angle=reference,
        angle_annotations=_angle_annotations(atoms, bonds, "a0", category, label, is_approximate=True),
        electron_domains=_electron_domains(atoms, bonds, "a0", record, label, template["lone_pairs"]),
        warning_vi="Mô hình 3D VSEPR lý tưởng chỉ dùng để minh họa; góc hiển thị được đo từ chính tọa độ này.",
        warning_en="This idealized VSEPR model is illustrative; displayed angles are measured from these coordinates.",
    )


def resolve_structure3d(record: dict[str, Any]) -> Structure3DResult:
    statuses: list[ExternalServiceStatus] = []
    reference = resolve_reference_angle(record)
    experimental = match_experimental_geometry(record)
    if experimental is not None:
        return Structure3DResult(_experimental(record, experimental, reference), tuple(statuses))
    cid = record.get("pubchem_cid")
    if cid:
        pubchem = fetch_pubchem_3d(int(cid))
        statuses.append(pubchem.status)
        if pubchem.data:
            structure = _from_block(record, pubchem.data, reference=reference, source=StructureSource.PUBCHEM_3D, source_label="PubChem 3D conformer", data_format="sdf", pubchem_cid=int(cid))
            if structure is not None:
                return Structure3DResult(structure, tuple(statuses))
    rdkit = generate_rdkit_result(record.get("smiles"))
    statuses.append(rdkit.status)
    if rdkit.structure:
        structure = _from_block(record, rdkit.structure.molblock, reference=reference, source=StructureSource.RDKIT_ETKDG, source_label=f"RDKit-generated conformer ({rdkit.structure.force_field})", data_format="molblock")
        if structure is not None:
            return Structure3DResult(structure, tuple(statuses))
    return Structure3DResult(_idealized(record, reference), tuple(statuses))


def get_structure3d(record: dict[str, Any]) -> Structure3D:
    """Backward-compatible structure-only API."""

    return resolve_structure3d(record).structure
