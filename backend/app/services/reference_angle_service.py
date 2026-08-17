"""Legacy single-angle summary and the curated shape target for idealized models.

Two distinct jobs live here, and neither is authoritative for geometry any more:

* :func:`molecule_specific_shape_target` supplies the one curated, molecule-specific
  angle an *idealized* model may be opened onto, so the arc measured from the drawn
  coordinates agrees with the number printed beside it. It applies only to the
  educational fallback; it never touches experimental or computed coordinates.
* :func:`resolve_reference_angle` fills the deprecated
  :class:`~app.schemas.structure3d_schema.ReferenceBondAngle` field. A geometry with
  several inequivalent angles resolves to ``None`` there, because one number cannot
  describe it -- that limitation is why geometry is now a collection of observations.

Nothing here keys off a formula: molecule-specific values come from the curated and
experimental datasets the rest of the pipeline already reads.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from app.chemistry.vsepr_rules import get_vsepr_rule
from app.schemas.structure3d_schema import ReferenceBondAngle

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from app.geometry.resolver import ResolvedGeometry

_NUMBER = re.compile(r"\d+(?:\.\d+)?")

CURATED_REFERENCE_SOURCE = "Curated molecule-specific teaching reference"


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


def molecule_specific_shape_target(record: dict[str, Any]) -> tuple[float | None, str | None]:
    """The curated angle an idealized model may be shaped to, with its source label."""

    label = curated_reference_label(record)
    value = _single_angle(label)
    if value is None:
        return None, None
    return value, CURATED_REFERENCE_SOURCE


def _experimental_reference(geometry: "ResolvedGeometry | None") -> ReferenceBondAngle | None:
    """Only when the experimental record has exactly one distinct angle."""

    if geometry is None or not geometry.is_experimental:
        return None
    values = {round(observation.value_deg, 4) for observation in geometry.evidence.bond_angles}
    if len(values) != 1:
        return None
    value = next(iter(values))
    return ReferenceBondAngle(
        value_deg=value,
        display_label=f"{value:.2f}°",
        category="measured",
        source=f"{geometry.evidence.source.name} experimental {geometry.evidence.phase or ''} geometry".strip(),
        is_approximate=False,
    )


def resolve_reference_angle(
    record: dict[str, Any],
    geometry: "ResolvedGeometry | None" = None,
) -> ReferenceBondAngle | None:
    """Resolve the deprecated single reference angle, or ``None`` when none applies."""

    experimental = _experimental_reference(geometry)
    if experimental is not None:
        return experimental

    curated_label = curated_reference_label(record)
    curated_value = _single_angle(curated_label)
    if curated_value is not None and curated_label is not None:
        return ReferenceBondAngle(
            value_deg=curated_value, display_label=curated_label, category="curated_reference",
            source=CURATED_REFERENCE_SOURCE, is_approximate=True,
        )

    rule = get_vsepr_rule(int(record["bonding_domains"]), int(record["lone_pair_domains"]))
    ideal_value = _single_angle(rule.ideal_angle)
    if ideal_value is None:
        return None
    return ReferenceBondAngle(
        value_deg=ideal_value, display_label=rule.ideal_angle, category="ideal_vsepr",
        source="General VSEPR prediction", is_approximate=True,
    )
