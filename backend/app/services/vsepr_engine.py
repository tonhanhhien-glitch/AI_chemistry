"""Deterministic VSEPR classification from verified domain counts."""

from typing import Any

from app.chemistry.hybridization import pedagogical_hybridization
from app.chemistry.vsepr_rules import get_vsepr_rule
from app.core.exceptions import ChemistryValidationError
from app.schemas.vsepr_schema import VSEPRResult


def analyze_vsepr(record: dict[str, Any]) -> VSEPRResult:
    bonding = int(record["bonding_domains"])
    lone_pairs = int(record["lone_pair_domains"])
    rule = get_vsepr_rule(bonding, lone_pairs)
    if record["ax_en"] != rule.ax_en:
        raise ChemistryValidationError("The AXnEm in the data does not match the electron-domain count.")
    if record["electron_geometry"] != rule.electron_geometry or record["molecular_geometry"] != rule.molecular_geometry:
        raise ChemistryValidationError("The geometry in the data does not match the VSEPR table.")
    hybridization, warning = pedagogical_hybridization(bonding + lone_pairs)
    return VSEPRResult(
        bonding_domains=bonding, lone_pair_domains=lone_pairs, steric_number=bonding + lone_pairs,
        ax_en=rule.ax_en, electron_geometry=rule.electron_geometry, electron_geometry_vi=rule.electron_geometry_vi,
        molecular_geometry=rule.molecular_geometry, molecular_geometry_vi=rule.molecular_geometry_vi,
        ideal_angle=rule.ideal_angle, distortion_note_vi=record.get("distortion_note_vi"),
        teaching_note_vi=record.get("teaching_note_vi") or rule.teaching_note_vi,
        pedagogical_hybridization=hybridization, hybridization_warning_vi=warning,
    )
