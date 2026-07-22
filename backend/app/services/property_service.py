"""Properties separated by provenance and verification role."""

from typing import Any

from app.schemas.molecule_schema import PropertyItem

_ATOMIC_WEIGHTS = {"H": 1.008, "B": 10.81, "C": 12.011, "N": 14.007, "O": 15.999, "F": 18.998, "P": 30.974, "S": 32.06, "Cl": 35.45, "Br": 79.904, "Xe": 131.293}


def get_properties(record: dict[str, Any]) -> list[PropertyItem]:
    mass = sum(_ATOMIC_WEIGHTS[symbol] * count for symbol, count in record["atom_inventory"].items())
    return [
        PropertyItem(key="molar_mass", label_vi="Molar mass computed from standard atomic weights", value=round(mass, 3), unit="g/mol", provenance="computed", note_vi="Value computed from elemental composition, not taken from an LLM."),
        PropertyItem(key="polarity", label_vi="Polarity note", value=record.get("polarity_note_en") or record["polarity_note_vi"], provenance="curated", verified_teaching_fact=True),
        PropertyItem(key="review_status", label_vi="Data review status", value=record["review_status"], provenance="curated", note_vi="Not labelled externally verified until an expert sign-off exists."),
    ]
