"""Select bond-angle evidence without conflating provenance.

Every angle offered to a student is derived from a
:class:`~app.schemas.structure3d_schema.BondAngleAnnotation` of the structure that is
actually rendered, so the number in the summary, the number on the arc and the drawn
geometry can never disagree. A geometry with several inequivalent angles produces
several entries, each with its own symmetry-equivalent count.
"""

from __future__ import annotations

from typing import Any

from app.chemistry.vsepr_rules import get_vsepr_rule
from app.schemas.bond_angle_schema import BondAngleEvidence, BondAnglesResult
from app.schemas.geometry_evidence_schema import GeometryEvidenceType
from app.schemas.structure3d_schema import Structure3D
from app.services.reference_angle_service import CURATED_REFERENCE_SOURCE, curated_reference_label, first_number

_EVIDENCE_TYPE_BY_GEOMETRY = {
    GeometryEvidenceType.EXPERIMENTAL: "experimental",
    GeometryEvidenceType.SOURCE_ANNOTATION: "curated_reference",
    GeometryEvidenceType.COMPUTED_CONFORMER: "computed_conformer",
    GeometryEvidenceType.DETERMINISTIC_CALCULATION: "computed_conformer",
    GeometryEvidenceType.IDEAL_VSEPR: "ideal_vsepr",
}


def build_bond_angles(record: dict[str, Any], structure: Structure3D) -> BondAnglesResult:
    atoms = {atom.id: atom for atom in structure.atoms}
    summary = structure.geometry_evidence
    coordinate_derived: list[BondAngleEvidence] = []
    for annotation in structure.angle_annotations:
        coordinate_derived.append(BondAngleEvidence(
            id=f"coordinate-{annotation.id}",
            atom1_element=atoms[annotation.atom1_id].element,
            center_element=atoms[annotation.center_atom_id].element,
            atom2_element=atoms[annotation.atom2_id].element,
            atom1_id=annotation.atom1_id,
            center_atom_id=annotation.center_atom_id,
            atom2_id=annotation.atom2_id,
            value_deg=annotation.value_deg,
            coordinate_value_deg=annotation.coordinate_value_deg,
            display_label=annotation.display_label,
            evidence_type=_EVIDENCE_TYPE_BY_GEOMETRY[annotation.evidence_type],
            source_name=summary.source_name if summary else structure.source_label,
            source_url=annotation.source_url,
            reference=annotation.source_reference,
            phase=annotation.phase,
            uncertainty_deg=annotation.uncertainty_deg,
            is_experimental=structure.is_experimental,
            is_computed=structure.is_computed,
            is_approximate=structure.is_illustrative,
            equivalent_count=annotation.equivalent_count,
            provenance_label_vi=summary.provenance_label_vi if summary else None,
            provenance_label_en=summary.provenance_label_en if summary else None,
        ))

    # An experimental structure's annotations *are* the experimental evidence: each one
    # carries the published value and has been validated against the drawn coordinates.
    experimental = [item for item in coordinate_derived if item.evidence_type == "experimental"]

    rule = get_vsepr_rule(int(record["bonding_domains"]), int(record["lone_pair_domains"]))
    outer = record["atom_symbols"][1] if len(record["atom_symbols"]) > 1 else "X"
    vsepr_prediction = [BondAngleEvidence(
        id=f"vsepr-{record['ax_en']}", atom1_element=outer, center_element=record["central_atom"], atom2_element=outer,
        value_deg=first_number(rule.ideal_angle), display_label=rule.ideal_angle, evidence_type="ideal_vsepr",
        source_name="General VSEPR prediction", is_approximate=True,
        provenance_label_vi="Minh họa VSEPR lý tưởng hóa", provenance_label_en="Idealized VSEPR illustration",
    )]

    curated: list[BondAngleEvidence] = []
    curated_label = curated_reference_label(record)
    if curated_label:
        curated = [BondAngleEvidence(
            id=f"curated-{record['id']}", atom1_element=outer, center_element=record["central_atom"], atom2_element=outer,
            value_deg=first_number(curated_label), display_label=curated_label, evidence_type="curated_reference",
            source_name=CURATED_REFERENCE_SOURCE, is_approximate=True,
            provenance_label_vi="Chú giải từ nguồn dữ liệu", provenance_label_en="Source-derived annotation",
        )]

    if experimental:
        preferred = experimental
        reason = (
            f"Experimental geometry from {experimental[0].source_name} is the highest-priority evidence; "
            f"{len(experimental)} inequivalent angle(s) were measured."
        )
    elif curated:
        preferred, reason = curated, "A curated molecule-specific teaching reference is available."
    elif not structure.is_illustrative and coordinate_derived:
        preferred, reason = coordinate_derived, "No experimental record exists; the preferred value is calculated from the active computed conformer."
    else:
        preferred, reason = vsepr_prediction, "No molecule-specific measurement or conformer is available; showing the general VSEPR estimate."
    return BondAnglesResult(
        preferred=preferred, experimental=experimental, coordinate_derived=coordinate_derived,
        vsepr_prediction=vsepr_prediction, curated_reference=curated, selection_reason=reason,
    )
