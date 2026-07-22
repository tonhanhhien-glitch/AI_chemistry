"""Structured octet-exception classification."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OctetException:
    electron_deficient: bool = False
    expanded_octet: bool = False
    odd_electron: bool = False
    note_vi: str | None = None


def classify_octet_exception(
    *, central_electrons: int, total_valence: int, central_period: int
) -> OctetException:
    electron_deficient = central_electrons < 8
    expanded = central_period >= 3 and central_electrons > 8
    odd = total_valence % 2 == 1
    notes: list[str] = []
    if electron_deficient:
        notes.append("The central atom does not have a complete octet.")
    if expanded:
        notes.append(
            "The Lewis representation uses an expanded octet for period-3+ atoms."
        )
    if odd:
        notes.append("The total number of valence electrons is odd.")
    return OctetException(
        electron_deficient, expanded, odd, " ".join(notes) or None
    )
