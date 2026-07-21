"""Validate that explanatory text does not contradict immutable rule output."""

import re
from typing import Any

_GEOMETRIES = {
    "linear", "trigonal planar", "bent", "tetrahedral", "trigonal pyramidal",
    "trigonal bipyramidal", "seesaw", "T-shaped", "octahedral",
    "square pyramidal", "square planar",
}


def validate_explanation_text(text: str, record: dict[str, Any]) -> tuple[bool, list[str]]:
    problems: list[str] = []
    normalized = text.casefold()
    if record["formula"].casefold() not in normalized:
        problems.append("missing_formula")
    notations = set(re.findall(r"AX\d(?:E\d)?", text, flags=re.IGNORECASE))
    if notations and {item.upper() for item in notations} != {record["ax_en"].upper()}:
        problems.append("contradictory_ax_en")
    mentioned_geometries = {geometry for geometry in _GEOMETRIES if geometry.casefold() in normalized}
    allowed = {record["electron_geometry"], record["molecular_geometry"]}
    if mentioned_geometries - allowed:
        problems.append("contradictory_geometry")
    expected_numbers = set(re.findall(r"\d+(?:\.\d+)?", record["ideal_angle"]))
    angle_numbers = set(re.findall(r"(\d+(?:\.\d+)?)\s*°", text))
    if angle_numbers and not angle_numbers.issubset(expected_numbers):
        problems.append("contradictory_angle")
    return not problems, problems
