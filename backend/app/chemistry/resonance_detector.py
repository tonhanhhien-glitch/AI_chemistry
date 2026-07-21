"""Curated resonance metadata; no arbitrary structure enumeration claim."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResonanceInfo:
    has_resonance: bool
    equivalent_forms: int
    note_vi: str | None = None


def curated_resonance(record: dict[str, object]) -> ResonanceInfo:
    forms = int(record.get("resonance_forms", 1))
    note = record.get("resonance_note_vi")
    return ResonanceInfo(forms > 1, forms, str(note) if note else None)
