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
    electron_counts = {
        int(value)
        for value in re.findall(
            r"(\d+)\s+(?:electron hoá trị|valence electrons)", normalized
        )
    }
    if electron_counts != {record["total_valence_electrons"]}:
        problems.append("missing_or_contradictory_valence_total")
    charge_values = {
        int(value)
        for value in re.findall(
            r"(?:điện tích hình thức|formal charges?)[^.\d+-]{0,30}"
            r"(?:bằng|sum(?:ming)? to)?\s*([+-]?\d+)",
            normalized,
        )
    }
    if charge_values != {record["charge"]}:
        problems.append("missing_or_contradictory_charge")
    bonding = {int(value) for value in re.findall(r"(\d+)\s+(?:miền liên kết|bonding domains?)", normalized)}
    lone_pairs = {int(value) for value in re.findall(r"(\d+)\s+(?:miền (?:cặp electron )?tự do|lone-pair domains?)", normalized)}
    if bonding != {record["bonding_domains"]}:
        problems.append("missing_or_contradictory_bonding_domains")
    if lone_pairs != {record["lone_pair_domains"]}:
        problems.append("missing_or_contradictory_lone_pair_domains")
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
