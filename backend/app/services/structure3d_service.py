"""Build the rendered 3D structure from resolved geometry evidence.

The resolution priority itself lives in :mod:`app.geometry.resolver`. This module's
job is to turn the winning evidence -- and the coordinates that were validated
against it -- into the :class:`Structure3D` the API returns, with:

* every angle annotation measured from the coordinates that will actually be drawn,
* the source's published value shown when the coordinates reproduce it,
* symmetry-equivalent angles grouped with an explicit equivalent count,
* a provenance block that never calls a computed conformer experimental.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from typing import Any

from app.geometry.fitter import angle_degrees
from app.geometry.providers.base import GeometryQuery
from app.geometry.providers.ideal_vsepr import normalize as _normalize
from app.geometry.providers.ideal_vsepr import reshape_ligands as _reshape_ligands
from app.geometry.providers.ideal_vsepr import templates as _templates
from app.geometry.resolver import ResolvedGeometry, resolve_geometry
from app.schemas.geometry_evidence_schema import (
    GeometryEvidenceSummary,
    GeometryEvidenceType,
    GeometryLengthSummary,
    MolecularGeometryEvidence,
)
from app.schemas.molecule_schema import ExternalServiceStatus
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
from app.services.reference_angle_service import molecule_specific_shape_target, resolve_reference_angle

__all__ = [
    "Structure3DResult",
    "calculate_angle",
    "get_structure3d",
    "resolve_structure3d",
    "_angle_annotations",
    "_reshape_ligands",
    "_templates",
]

#: Angles this close together are the same symmetry-equivalent angle.
ANGLE_GROUPING_TOLERANCE_DEG = 0.01

_SOURCE_BY_PROVIDER = {
    "nist_cccbdb": StructureSource.EXPERIMENTAL_GEOMETRY,
    "pubchem_3d": StructureSource.PUBCHEM_3D,
    "rdkit_etkdg": StructureSource.RDKIT_ETKDG,
    "ideal_vsepr": StructureSource.IDEALIZED_VSEPR,
}

_CATEGORY_BY_EVIDENCE = {
    GeometryEvidenceType.EXPERIMENTAL: "measured",
    GeometryEvidenceType.SOURCE_ANNOTATION: "curated_reference",
    GeometryEvidenceType.COMPUTED_CONFORMER: "conformer",
    GeometryEvidenceType.DETERMINISTIC_CALCULATION: "conformer",
    GeometryEvidenceType.IDEAL_VSEPR: "ideal_vsepr",
}

_PROVENANCE_LABELS = {
    GeometryEvidenceType.EXPERIMENTAL: ("Phép đo thực nghiệm", "Experimental measurement"),
    GeometryEvidenceType.SOURCE_ANNOTATION: ("Chú giải từ nguồn dữ liệu", "Source-derived annotation"),
    GeometryEvidenceType.COMPUTED_CONFORMER: ("Cấu dạng tính toán", "Computed conformer"),
    GeometryEvidenceType.DETERMINISTIC_CALCULATION: ("Tính toán tất định", "Deterministic calculation"),
    GeometryEvidenceType.IDEAL_VSEPR: ("Minh họa VSEPR lý tưởng hóa", "Idealized VSEPR illustration"),
}


@dataclass(frozen=True, slots=True)
class Structure3DResult:
    structure: Structure3D
    statuses: tuple[ExternalServiceStatus, ...] = ()
    geometry: ResolvedGeometry | None = None


def _xyz(atom: Structure3DAtom) -> tuple[float, float, float]:
    return atom.x, atom.y, atom.z


def calculate_angle(
    atom_a: Structure3DAtom,
    central_atom: Structure3DAtom,
    atom_b: Structure3DAtom,
) -> float:
    """Calculate A-center-B in degrees without display-time rounding."""

    return angle_degrees(_xyz(atom_a), _xyz(central_atom), _xyz(atom_b))


def _format_angle(value: float, evidence_type: GeometryEvidenceType) -> str:
    """Measurements keep the precision they were published at; models do not pretend to."""

    decimals = 2 if evidence_type is GeometryEvidenceType.EXPERIMENTAL else 1
    return f"{value:.{decimals}f}°"


def _angle_annotations(
    atoms: list[Structure3DAtom],
    bonds: list[Structure3DBond],
    center_id: str,
    category: str,
    source: str,
    *,
    is_approximate: bool | None = None,
    evidence: MolecularGeometryEvidence | None = None,
    evidence_type: GeometryEvidenceType | None = None,
) -> list[BondAngleAnnotation]:
    """Group the angles of the drawn coordinates, attaching any matching source value."""

    resolved_type = evidence_type or (evidence.evidence_type if evidence else GeometryEvidenceType.IDEAL_VSEPR)
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
        match_index = next(
            (index for index, existing in enumerate(representatives) if abs(value - existing[0]) < ANGLE_GROUPING_TOLERANCE_DEG),
            None,
        )
        if match_index is None:
            representatives.append((value, atom1_id, atom2_id, 1))
        else:
            existing = representatives[match_index]
            representatives[match_index] = (*existing[:3], existing[3] + 1)

    # Only an independent source has a value worth showing over the coordinate
    # measurement. A computed or idealized geometry's "observations" were derived from
    # these very coordinates, so quoting them back would add provenance that is not real.
    observations = {}
    if evidence is not None and resolved_type in {GeometryEvidenceType.EXPERIMENTAL, GeometryEvidenceType.SOURCE_ANNOTATION}:
        for observation in evidence.bond_angles:
            key = (frozenset({observation.atom1_id, observation.atom2_id}), observation.center_atom_id)
            observations[key] = observation

    annotations: list[BondAngleAnnotation] = []
    for index, (value, atom1_id, atom2_id, equivalent_count) in enumerate(representatives):
        observation = observations.get((frozenset({atom1_id, atom2_id}), center_id))
        source_value = observation.value_deg if observation is not None else None
        deviation = abs(source_value - value) if source_value is not None else None
        display_value = source_value if source_value is not None else value
        annotations.append(BondAngleAnnotation(
            id=f"angle-{index}",
            atom1_id=atom1_id,
            center_atom_id=center_id,
            atom2_id=atom2_id,
            value_deg=display_value,
            coordinate_value_deg=value,
            source_value_deg=source_value,
            deviation_deg=deviation,
            uncertainty_deg=observation.uncertainty_deg if observation is not None else None,
            display_label=_format_angle(display_value, resolved_type),
            category=category,
            evidence_type=resolved_type,
            source=source,
            source_reference=evidence.source.reference if evidence else None,
            source_url=evidence.source.url if evidence else None,
            phase=evidence.phase if evidence else None,
            is_approximate=category == "ideal_vsepr" if is_approximate is None else is_approximate,
            equivalent_count=equivalent_count,
            note_vi="Góc được tính trực tiếp từ tọa độ đang hiển thị.",
            note_en="Angle calculated directly from the rendered coordinates.",
        ))
    return annotations


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
    elif lone_pair_count:
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


def _align_bond_orders(ligand_elements: list[str], record: dict[str, Any]) -> list[int]:
    """Map the record's bond orders onto the geometry's ligand order, by element.

    The geometry source decides the atom order; the deterministic layer decides the
    bond orders. Matching them per element keeps both authorities intact.
    """

    symbols = list(record.get("atom_symbols") or [])[1:]
    orders = list(record.get("bond_orders") or [])
    if len(symbols) != len(orders) or Counter(symbols) != Counter(ligand_elements):
        return [1] * len(ligand_elements)
    pools: dict[str, list[int]] = {}
    for symbol, order in zip(symbols, orders, strict=True):
        pools.setdefault(symbol, []).append(int(order))
    for values in pools.values():
        values.sort(reverse=True)
    return [pools[element].pop(0) for element in ligand_elements]


def _summary(geometry: ResolvedGeometry) -> GeometryEvidenceSummary:
    evidence = geometry.evidence
    grouped: list[GeometryLengthSummary] = []
    for observation in evidence.bond_lengths:
        label = observation.label or "bond"
        match = next(
            (item for item in grouped if item.label == label and abs(item.value_angstrom - observation.value_angstrom) < 5e-4),
            None,
        )
        if match is None:
            grouped.append(GeometryLengthSummary(
                label=label, value_angstrom=round(observation.value_angstrom, 4),
                uncertainty_angstrom=observation.uncertainty_angstrom, equivalent_count=1,
            ))
        else:
            grouped[grouped.index(match)] = match.model_copy(update={"equivalent_count": match.equivalent_count + 1})
    label_vi, label_en = _PROVENANCE_LABELS[evidence.evidence_type]
    return GeometryEvidenceSummary(
        id=evidence.id,
        evidence_type=evidence.evidence_type,
        provider=geometry.provider_name,
        source_name=evidence.source.name,
        source_reference=evidence.source.reference,
        source_url=evidence.source.url,
        source_comments=evidence.source.comments,
        retrieved_at=evidence.source.retrieved_at,
        phase=evidence.phase,
        electronic_state=evidence.electronic_state,
        conformation=evidence.conformation,
        point_group=evidence.point_group,
        bond_lengths=grouped,
        bond_length_count=len(evidence.bond_lengths),
        bond_angle_count=len(evidence.bond_angles),
        dihedral_count=len(evidence.dihedrals),
        coordinates_are_fitted=evidence.coordinates is None,
        max_length_deviation_angstrom=geometry.fit.max_length_deviation,
        max_angle_deviation_deg=geometry.fit.max_angle_deviation,
        is_experimental=geometry.is_experimental,
        is_computed=geometry.is_computed,
        is_ideal=geometry.is_ideal,
        provenance_label_vi=label_vi,
        provenance_label_en=label_en,
    )


def _warnings(geometry: ResolvedGeometry) -> tuple[str, str]:
    evidence = geometry.evidence
    if geometry.is_experimental:
        return (
            f"Tọa độ nguyên tử là hình học {evidence.phase or 'thực nghiệm'} đo được từ {evidence.source.name}; "
            "các miền cặp electron tự do vẫn chỉ là lớp minh họa VSEPR.",
            f"Atomic coordinates are an experimental {evidence.phase or ''} geometry from {evidence.source.name}; "
            "lone-pair domains remain illustrative VSEPR overlays.",
        )
    if geometry.is_computed:
        return (
            f"Tọa độ là cấu dạng TÍNH TOÁN từ {evidence.source.name}, không phải phép đo thực nghiệm; "
            "các miền cặp electron tự do chỉ là lớp minh họa VSEPR.",
            f"Coordinates are a COMPUTED conformer from {evidence.source.name}, not an experimental measurement; "
            "lone-pair domains are only an illustrative VSEPR overlay.",
        )
    return (
        "Mô hình 3D VSEPR lý tưởng hóa chỉ dùng để minh họa, không phải số liệu đo; "
        "góc hiển thị được đo từ chính tọa độ này.",
        "This idealized VSEPR model is an educational illustration, not measured data; "
        "displayed angles are measured from these coordinates.",
    )


def _build_structure(
    record: dict[str, Any],
    geometry: ResolvedGeometry,
    reference: ReferenceBondAngle | None,
    shape_target: tuple[float | None, str | None] = (None, None),
) -> Structure3D:
    evidence = geometry.evidence
    atoms = [
        Structure3DAtom(id=item.id, element=item.element, x=item.x, y=item.y, z=item.z)
        for item in geometry.coordinates
    ]
    center_id = evidence.center_atom_id or atoms[0].id
    ligand_ids = [atom.id for atom in atoms if atom.id != center_id]
    ligand_elements = [atom.element for atom in atoms if atom.id != center_id]
    orders = _align_bond_orders(ligand_elements, record)
    bonds = [
        Structure3DBond(atom1_id=center_id, atom2_id=atom_id, order=order)
        for atom_id, order in zip(ligand_ids, orders, strict=True)
    ]
    label = _structure_label(geometry, shape_target)
    category = _CATEGORY_BY_EVIDENCE[evidence.evidence_type]
    template_lone_pairs = (
        _templates()[record["ax_en"]]["lone_pairs"]
        if geometry.is_ideal and record.get("ax_en") in _templates() else None
    )
    warning_vi, warning_en = _warnings(geometry)
    return Structure3D(
        atoms=atoms,
        bonds=bonds,
        source=_SOURCE_BY_PROVIDER.get(geometry.provider_name, StructureSource.IDEALIZED_VSEPR),
        source_label=label,
        evidence_type=evidence.evidence_type,
        geometry_evidence=_summary(geometry),
        is_illustrative=geometry.is_ideal,
        is_computed=geometry.is_computed,
        is_experimental=geometry.is_experimental,
        pubchem_cid=evidence.identity.pubchem_cid,
        central_atom_id=center_id,
        reference_bond_angle=reference,
        angle_annotations=_angle_annotations(
            atoms, bonds, center_id, category, label,
            is_approximate=geometry.is_ideal,
            evidence=evidence,
        ),
        electron_domains=_electron_domains(atoms, bonds, center_id, record, label, template_lone_pairs),
        warning_vi=warning_vi,
        warning_en=warning_en,
    )


def _structure_label(geometry: ResolvedGeometry, shape_target: tuple[float | None, str | None] = (None, None)) -> str:
    evidence = geometry.evidence
    if geometry.is_experimental:
        phase = f" {evidence.phase}-phase" if evidence.phase else ""
        return f"{evidence.source.name} experimental{phase} geometry"
    if geometry.provider_name == "pubchem_3d":
        return "PubChem 3D conformer"
    if geometry.provider_name == "rdkit_etkdg":
        force_field = (evidence.source.reference or "").split(",")[-1].strip() or "RDKit"
        return f"RDKit-generated conformer ({force_field})"
    target, _source = shape_target
    if target is not None:
        return f"Idealized VSEPR model at the {target}° reference angle"
    return "Idealized VSEPR model"


def resolve_structure3d(record: dict[str, Any]) -> Structure3DResult:
    """Resolve the geometry to render, experimental evidence first."""

    shape_target = molecule_specific_shape_target(record)
    geometry = resolve_geometry(
        GeometryQuery.from_record(record),
        ideal_shape_target_deg=shape_target[0],
        ideal_shape_source=shape_target[1],
    )
    reference = resolve_reference_angle(record, geometry)
    structure = _build_structure(record, geometry, reference, shape_target)
    return Structure3DResult(structure, geometry.statuses, geometry)


def get_structure3d(record: dict[str, Any]) -> Structure3D:
    """Backward-compatible structure-only API."""

    return resolve_structure3d(record).structure
