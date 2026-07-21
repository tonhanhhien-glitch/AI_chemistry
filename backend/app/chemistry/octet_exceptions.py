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
        notes.append("Nguyên tử trung tâm chưa đủ bát tử.")
    if expanded:
        notes.append(
            "Biểu diễn Lewis dùng bát tử mở rộng cho nguyên tử chu kỳ 3 trở lên."
        )
    if odd:
        notes.append("Tổng electron hoá trị là số lẻ.")
    return OctetException(
        electron_deficient, expanded, odd, " ".join(notes) or None
    )
