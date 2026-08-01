"""Properties separated by provenance and verification role."""

from typing import Any

from app.schemas.molecule_schema import PropertyItem

_ATOMIC_WEIGHTS = {"H": 1.008, "B": 10.81, "C": 12.011, "N": 14.007, "O": 15.999, "F": 18.998, "Al": 26.982, "Si": 28.085, "P": 30.974, "S": 32.06, "Cl": 35.45, "Br": 79.904, "I": 126.904, "Xe": 131.293}


def get_properties(record: dict[str, Any]) -> list[PropertyItem]:
    mass = sum(_ATOMIC_WEIGHTS[symbol] * count for symbol, count in record["atom_inventory"].items())
    curated = record["source"] == "curated"
    items = [
        PropertyItem(key="molar_mass", label_vi="Molar mass computed from standard atomic weights", value=round(mass, 3), unit="g/mol", provenance="computed", note_vi="Value computed from elemental composition, not taken from an LLM."),
    ]
    if record.get("molecular_weight") is not None:
        items.append(PropertyItem(key="pubchem_molecular_weight", label_vi="PubChem molecular weight", value=record["molecular_weight"], unit="g/mol", provenance="PubChem reference", note_vi="Reference property returned with the validated PubChem identity."))
    items.extend([
        PropertyItem(key="polarity", label_vi="Polarity note", value=record.get("polarity_note_en") or record["polarity_note_vi"], provenance="curated" if curated else "computed", verified_teaching_fact=curated, note_vi=None if curated else "No polarity conclusion was inferred for this uncurated record."),
        PropertyItem(key="review_status", label_vi="Data review status", value=record["review_status"], provenance="curated" if curated else "PubChem reference", note_vi="Not labelled externally verified until an expert sign-off exists."),
    ])
    return items
