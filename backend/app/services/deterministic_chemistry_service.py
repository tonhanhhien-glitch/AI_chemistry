"""Conservative Lewis/VSEPR inference for validated single-center main-group species."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from app.chemistry.central_atom_rules import choose_central_atom
from app.chemistry.formal_charge import calculate_formal_charge, validate_formal_charge_sum
from app.chemistry.periodic_table import get_valence_electrons
from app.chemistry.valence_rules import total_valence_electrons
from app.chemistry.vsepr_rules import get_vsepr_rule
from app.core.exceptions import ChemistryValidationError
from app.schemas.molecule_schema import PubChemCandidate
from app.services.formula_parser import ParsedFormula

_TOKEN = re.compile(r"Cl|Br|[A-Z][a-z]?|\(|\)|=|#|-")
_TERMINAL_SINGLE_BOND = frozenset({"H", "F", "Cl", "Br", "I"})


def _simple_smiles_graph(smiles: str) -> tuple[list[str], list[tuple[int, int, int]]]:
    """Parse only acyclic, explicit single-center SMILES; reject everything else."""

    compact = smiles.strip()
    matches = list(_TOKEN.finditer(compact))
    if not matches or "".join(match.group(0) for match in matches) != compact:
        raise ChemistryValidationError("The validated connectivity uses unsupported SMILES syntax.")
    atoms: list[str] = []
    bonds: list[tuple[int, int, int]] = []
    branch_stack: list[int] = []
    current: int | None = None
    pending_order = 1
    for match in matches:
        token = match.group(0)
        if token == "(":
            if current is None:
                raise ChemistryValidationError("Invalid branch in connectivity.")
            branch_stack.append(current)
        elif token == ")":
            if not branch_stack:
                raise ChemistryValidationError("Invalid branch in connectivity.")
            current = branch_stack.pop()
        elif token in {"-", "=", "#"}:
            pending_order = {"-": 1, "=": 2, "#": 3}[token]
        else:
            new_index = len(atoms)
            atoms.append(token)
            if current is not None:
                bonds.append((current, new_index, pending_order))
            current = new_index
            pending_order = 1
    if branch_stack or len(bonds) != len(atoms) - 1:
        raise ChemistryValidationError("Only an acyclic covalent unit is supported automatically.")
    return atoms, bonds


def build_deterministic_record(parsed: ParsedFormula, candidate: PubChemCandidate | None = None) -> dict[str, Any]:
    """Return a record compatible with existing Lewis/VSEPR services or fail safely."""

    if sum(parsed.atoms.values()) < 3 or sum(parsed.atoms.values()) > 7:
        raise ChemistryValidationError("Automatic inference supports three to seven atoms in one covalent unit.")
    central = choose_central_atom(parsed.atoms)
    if parsed.atoms.get(central) != 1:
        raise ChemistryValidationError("Automatic inference requires exactly one central atom.")
    outer_symbols = [symbol for symbol, count in parsed.atoms.items() if symbol != central for _ in range(count)]
    if not outer_symbols or any(symbol not in _TERMINAL_SINGLE_BOND for symbol in outer_symbols):
        raise ChemistryValidationError("Automatic inference supports only unambiguous terminal H/halogen single bonds.")

    smiles = (candidate.canonical_smiles or candidate.isomeric_smiles) if candidate else None
    if smiles:
        graph_atoms, graph_bonds = _simple_smiles_graph(smiles)
        if Counter(graph_atoms) != Counter(parsed.atoms):
            raise ChemistryValidationError("Connectivity atom inventory does not match the formula.")
        central_indexes = [index for index, symbol in enumerate(graph_atoms) if symbol == central]
        if len(central_indexes) != 1:
            raise ChemistryValidationError("Connectivity does not contain a unique central atom.")
        center_index = central_indexes[0]
        degrees = Counter()
        for atom1, atom2, order in graph_bonds:
            if order != 1 or center_index not in {atom1, atom2}:
                raise ChemistryValidationError("Connectivity is not a supported single-center star graph.")
            degrees[atom1] += 1
            degrees[atom2] += 1
        if degrees[center_index] != len(outer_symbols) or any(degrees[index] != 1 for index in range(len(graph_atoms)) if index != center_index):
            raise ChemistryValidationError("Connectivity is not a supported single-center star graph.")

    total = total_valence_electrons(parsed.atoms, parsed.charge)
    bond_orders = [1] * len(outer_symbols)
    outer_lone_pairs = [0 if symbol == "H" else 3 for symbol in outer_symbols]
    remaining = total - 2 * sum(bond_orders) - 2 * sum(outer_lone_pairs)
    if remaining < 0 or remaining % 2:
        raise ChemistryValidationError("The electron count does not yield a closed-shell Lewis structure.")
    central_lone_pairs = remaining // 2
    if central_lone_pairs > 3:
        raise ChemistryValidationError("The central lone-pair count is outside the supported VSEPR scope.")
    bonding_domains = len(outer_symbols)
    rule = get_vsepr_rule(bonding_domains, central_lone_pairs)

    atom_symbols = [central, *outer_symbols]
    lone_pairs = [central_lone_pairs, *outer_lone_pairs]
    formal_charges = [
        calculate_formal_charge(symbol, 2 * lone_pair_count, 2 * bond_order_sum)
        for symbol, lone_pair_count, bond_order_sum in zip(
            atom_symbols,
            lone_pairs,
            [sum(bond_orders), *bond_orders],
            strict=True,
        )
    ]
    validate_formal_charge_sum(formal_charges, parsed.charge)
    center_shell_electrons = 2 * sum(bond_orders) + 2 * central_lone_pairs
    if candidate:
        title = candidate.iupac_name or candidate.title or f"PubChem CID {candidate.cid}"
        record_id = candidate.id
        source = "PubChem reference"
        review_status = "pubchem_identity_deterministic_chemistry_unreviewed"
        pubchem_cid = candidate.cid
        inchi = candidate.inchi
        inchikey = candidate.inchikey
        canonical_identity = candidate.inchikey or f"PubChem CID {candidate.cid}"
        validation_status = "formula_charge_inventory_connectivity_lewis_vsepr_validated"
        cache_timestamp = candidate.cache_timestamp
        molecular_weight = candidate.molecular_weight
    else:
        title = parsed.formula
        record_id = f"deterministic:{parsed.formula.casefold()}"
        source = "deterministic"
        review_status = "deterministic_formula_scope_unreviewed"
        pubchem_cid = None
        inchi = inchikey = canonical_identity = cache_timestamp = molecular_weight = None
        validation_status = "formula_unique_scope_lewis_vsepr_validated"
    return {
        "id": record_id,
        "formula": parsed.formula,
        "name_vi": title,
        "name_en": title,
        "aliases": [],
        "charge": parsed.charge,
        "atom_inventory": parsed.atoms,
        "atom_symbols": atom_symbols,
        "central_atom": central,
        "total_valence_electrons": total,
        "bond_orders": bond_orders,
        "lone_pairs": lone_pairs,
        "formal_charges": formal_charges,
        "resonance_forms": 1,
        "resonance_note_vi": None,
        "resonance_note_en": None,
        "exception_flags": {
            "electron_deficient": center_shell_electrons < 8,
            "expanded_octet": center_shell_electrons > 8,
            "odd_electron": False,
        },
        "bonding_domains": bonding_domains,
        "lone_pair_domains": central_lone_pairs,
        "steric_number": bonding_domains + central_lone_pairs,
        "ax_en": rule.ax_en,
        "electron_geometry": rule.electron_geometry,
        "electron_geometry_vi": rule.electron_geometry_vi,
        "molecular_geometry": rule.molecular_geometry,
        "molecular_geometry_vi": rule.molecular_geometry_vi,
        "ideal_angle": rule.ideal_angle,
        "distortion_note_vi": "Giá trị tham chiếu VSEPR có thể khác góc đo từ cấu dạng 3D.",
        "distortion_note_en": "The VSEPR teaching reference may differ from the angle measured in the 3D conformer.",
        "teaching_note_vi": rule.teaching_note_vi,
        "teaching_note_en": rule.teaching_note_en,
        "polarity_note_vi": "Không tự động suy luận độ phân cực cho bản ghi chưa được tuyển chọn.",
        "polarity_note_en": "Polarity is not inferred automatically for an uncurated PubChem record.",
        "review_status": review_status,
        "source": source,
        "confidence": "medium",
        "pubchem_cid": pubchem_cid,
        "smiles": smiles,
        "inchi": inchi,
        "inchikey": inchikey,
        "canonical_identity": canonical_identity,
        "validation_status": validation_status,
        "cache_timestamp": cache_timestamp,
        "molecular_weight": molecular_weight,
    }
