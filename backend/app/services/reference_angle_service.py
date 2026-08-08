"""Pick the one molecule-specific bond angle that the summary and the 3D overlay share.

Priority, highest first:

1. a local experimental gas-phase geometry (the NIST CCCBDB snapshot),
2. a trusted molecule-specific conformer -- PubChem or RDKit coordinates, measured directly
   by :mod:`app.services.structure3d_service`, so it needs no entry here,
3. a curated molecule-specific teaching reference: the ``ideal_angle`` of a curated record,
   used only where it actually departs from the generic AXnEm label,
4. the generic AXnEm ideal angle, as a fallback only.

Nothing here keys off a formula: every molecule-specific value comes from the curated and
experimental datasets the rest of the pipeline already reads, so adding a molecule to those
datasets is enough to give it a specific angle.
"""

from __future__ import annotations

import re
from typing import Any

from app.chemistry.vsepr_rules import get_vsepr_rule
from app.schemas.structure3d_schema import ReferenceBondAngle
from app.services.experimental_geometry_service import match_experimental_geometry

_NUMBER = re.compile(r"\d+(?:\.\d+)?")


def first_number(label: str | None) -> float | None:
    """First numeric value in a display label such as ``~104.5°`` or ``<109.5°``."""

    match = _NUMBER.search(label or "")
    return float(match.group()) if match else None


def _single_angle(label: str | None) -> float | None:
    """Value of a label that names exactly one angle; ``None`` for ``90°, 120°, 180°``."""

    numbers = _NUMBER.findall(label or "")
    return float(numbers[0]) if len(numbers) == 1 else None


def curated_reference_label(record: dict[str, Any]) -> str | None:
    """The record's ``ideal_angle`` when it is a molecule-specific override of the AXnEm rule."""

    if record.get("source") != "curated":
        return None
    label = record.get("ideal_angle")
    rule = get_vsepr_rule(int(record["bonding_domains"]), int(record["lone_pair_domains"]))
    return label if label and label != rule.ideal_angle else None


def resolve_reference_angle(record: dict[str, Any]) -> ReferenceBondAngle | None:
    """Resolve the reference angle for a record, or ``None`` when no single angle applies.

    Geometries with several inequivalent angles (trigonal bipyramidal, octahedral, ...) have
    no single reference value, so they resolve to ``None`` rather than to the first number of
    a label like ``90°, 120°, 180°``.
    """

    experimental = match_experimental_geometry(record)
    if experimental is not None:
        return ReferenceBondAngle(
            value_deg=experimental.experimental_angle_deg,
            display_label=f"{experimental.experimental_angle_deg:.2f}°",
            category="measured",
            source=f"{experimental.source_name} experimental gas-phase geometry",
            is_approximate=False,
        )

    curated_label = curated_reference_label(record)
    curated_value = _single_angle(curated_label)
    if curated_value is not None and curated_label is not None:
        return ReferenceBondAngle(
            value_deg=curated_value, display_label=curated_label, category="curated_reference",
            source="Curated molecule-specific teaching reference", is_approximate=True,
        )

    rule = get_vsepr_rule(int(record["bonding_domains"]), int(record["lone_pair_domains"]))
    ideal_value = _single_angle(rule.ideal_angle)
    if ideal_value is None:
        return None
    return ReferenceBondAngle(
        value_deg=ideal_value, display_label=rule.ideal_angle, category="ideal_vsepr",
        source="General VSEPR prediction", is_approximate=True,
    )
