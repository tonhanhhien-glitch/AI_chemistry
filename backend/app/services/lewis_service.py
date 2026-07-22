"""Build and validate frontend-ready Lewis structures from curated connectivity."""

import math
from typing import Any

from app.chemistry.formal_charge import validate_formal_charge_sum
from app.chemistry.valence_rules import total_valence_electrons
from app.core.exceptions import ChemistryValidationError
from app.schemas.lewis_schema import LewisAtom, LewisBond, LewisStructure, OctetExceptionFlags


def _positions(count: int) -> list[tuple[float, float]]:
    if count == 2:
        return [(55.0, 140.0), (265.0, 140.0)]
    radius = 105.0
    return [(160.0 + radius * math.cos(-math.pi / 2 + 2 * math.pi * i / count), 140.0 + radius * math.sin(-math.pi / 2 + 2 * math.pi * i / count)) for i in range(count)]


def build_lewis_structure(record: dict[str, Any]) -> LewisStructure:
    symbols = record["atom_symbols"]
    orders = record["bond_orders"]
    lone_pairs = record["lone_pairs"]
    charges = record["formal_charges"]
    if not (len(symbols) == len(lone_pairs) == len(charges)):
        raise ChemistryValidationError("Lewis atom data is inconsistent.")
    if len(orders) != len(symbols) - 1:
        raise ChemistryValidationError("The Lewis bond framework is inconsistent.")
    computed_total = total_valence_electrons(record["atom_inventory"], record["charge"])
    represented_total = 2 * sum(orders) + 2 * sum(lone_pairs)
    if computed_total != record["total_valence_electrons"] or represented_total != computed_total:
        raise ChemistryValidationError("The Lewis representation does not conserve valence electrons.")
    validate_formal_charge_sum(charges, record["charge"])
    positions = [(160.0, 140.0), *_positions(len(symbols) - 1)]
    atoms = [LewisAtom(id=f"a{i}", element=symbol, x=positions[i][0], y=positions[i][1], lone_pairs=lone_pairs[i], formal_charge=charges[i]) for i, symbol in enumerate(symbols)]
    bonds = [LewisBond(id=f"b{i}", atom1_id="a0", atom2_id=f"a{i + 1}", order=order) for i, order in enumerate(orders)]
    flags = dict(record["exception_flags"])
    notes = []
    if flags["electron_deficient"]:
        notes.append("The central atom is electron-deficient relative to the octet rule.")
    if flags["expanded_octet"]:
        notes.append("The Lewis representation uses an expanded octet.")
    if flags["odd_electron"]:
        notes.append("The species has an odd number of valence electrons.")
    return LewisStructure(
        atoms=atoms, bonds=bonds, central_atom_id="a0", total_valence_electrons=computed_total,
        resonance_forms=record.get("resonance_forms", 1), resonance_note_vi=record.get("resonance_note_vi"),
        exception_flags=OctetExceptionFlags(**flags, note_vi=" ".join(notes) or None), source="curated",
        confidence=record["confidence"], review_status=record["review_status"],
    )
