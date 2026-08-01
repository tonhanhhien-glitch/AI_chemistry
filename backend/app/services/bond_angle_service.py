"""Select molecule-specific bond-angle evidence without conflating provenance."""

import re
from typing import Any

from app.chemistry.vsepr_rules import get_vsepr_rule
from app.schemas.bond_angle_schema import BondAngleEvidence, BondAnglesResult
from app.schemas.structure3d_schema import Structure3D, StructureSource
from app.services.experimental_geometry_service import match_experimental_geometry


def _first_number(label: str) -> float | None:
    match = re.search(r"\d+(?:\.\d+)?", label)
    return float(match.group()) if match else None


def build_bond_angles(record: dict[str, Any], structure: Structure3D) -> BondAnglesResult:
    experimental_record = match_experimental_geometry(record)
    experimental: list[BondAngleEvidence] = []
    if experimental_record:
        pattern = experimental_record.angle_pattern
        experimental.append(BondAngleEvidence(
            id=f"experimental-{experimental_record.id}", atom1_element=pattern.atom1_element,
            center_element=pattern.center_element, atom2_element=pattern.atom2_element,
            value_deg=experimental_record.experimental_angle_deg,
            display_label=f"{experimental_record.experimental_angle_deg:.2f}°",
            evidence_type="experimental", source_name=experimental_record.source_name,
            source_url=experimental_record.source_url, reference=experimental_record.reference_label,
            phase=experimental_record.phase, is_experimental=True,
            equivalent_count=max(int(record["bonding_domains"] * (record["bonding_domains"] - 1) / 2), 1),
        ))

    atoms = {atom.id: atom for atom in structure.atoms}
    coordinate_derived: list[BondAngleEvidence] = []
    for annotation in structure.angle_annotations:
        evidence_type = "experimental" if structure.is_experimental else "ideal_vsepr" if structure.source is StructureSource.IDEALIZED_VSEPR else "computed_conformer"
        coordinate_derived.append(BondAngleEvidence(
            id=f"coordinate-{annotation.id}", atom1_element=atoms[annotation.atom1_id].element,
            center_element=atoms[annotation.center_atom_id].element, atom2_element=atoms[annotation.atom2_id].element,
            atom1_id=annotation.atom1_id, center_atom_id=annotation.center_atom_id, atom2_id=annotation.atom2_id,
            value_deg=annotation.value_deg, display_label=annotation.display_label, evidence_type=evidence_type,
            source_name=structure.source_label, is_experimental=structure.is_experimental,
            is_computed=structure.is_computed, is_approximate=structure.is_illustrative,
            equivalent_count=annotation.equivalent_count,
        ))

    rule = get_vsepr_rule(int(record["bonding_domains"]), int(record["lone_pair_domains"]))
    outer = record["atom_symbols"][1] if len(record["atom_symbols"]) > 1 else "X"
    vsepr_prediction = [BondAngleEvidence(
        id=f"vsepr-{record['ax_en']}", atom1_element=outer, center_element=record["central_atom"], atom2_element=outer,
        value_deg=_first_number(rule.ideal_angle), display_label=rule.ideal_angle, evidence_type="ideal_vsepr",
        source_name="General VSEPR prediction", is_approximate=True,
    )]

    curated: list[BondAngleEvidence] = []
    curated_label = record.get("ideal_angle")
    if record.get("source") == "curated" and curated_label and curated_label != rule.ideal_angle:
        curated = [BondAngleEvidence(
            id=f"curated-{record['id']}", atom1_element=outer, center_element=record["central_atom"], atom2_element=outer,
            value_deg=_first_number(curated_label), display_label=curated_label, evidence_type="curated_reference",
            source_name="Curated molecule-specific teaching reference", is_approximate=True,
        )]

    if experimental:
        preferred, reason = experimental, "Local experimental geometry is the highest-priority molecule-specific evidence."
    elif curated:
        preferred, reason = curated, "A curated molecule-specific teaching reference is available."
    elif structure.source is not StructureSource.IDEALIZED_VSEPR and coordinate_derived:
        preferred, reason = coordinate_derived, "No local reference exists; the preferred value is calculated from the active conformer."
    else:
        preferred, reason = vsepr_prediction, "No molecule-specific measurement or conformer is available; showing the general VSEPR estimate."
    return BondAnglesResult(preferred=preferred, experimental=experimental, coordinate_derived=coordinate_derived, vsepr_prediction=vsepr_prediction, selection_reason=reason)
