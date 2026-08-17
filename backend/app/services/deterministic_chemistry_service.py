"""Deterministic Lewis/VSEPR inference for single-centre main-group species.

This module used to gate its own capability on ``_TERMINAL_SINGLE_BOND`` -- a
whitelist of terminal elements -- and on a hand-written mini-SMILES regex. Both are
gone. Composition and charge now go to :mod:`app.chemistry.lewis_solver`, which
generates and ranks candidate structures under general chemical constraints, and
connectivity comes from :mod:`app.services.connectivity_service`, which uses real
parsers.

Connectivity, when available, is used to *check* the single-centre star topology.
It is never allowed to decide bond orders, formal charges, resonance or geometry:
those stay with the deterministic layer.
"""

from __future__ import annotations

from typing import Any

from app.chemistry.central_atom_rules import choose_central_atom
from app.chemistry.formal_charge import validate_formal_charge_sum
from app.chemistry.lewis_solver import LewisSolution, resonance_note, solve_lewis
from app.chemistry.vsepr_rules import get_vsepr_rule
from app.core.exceptions import ChemistryValidationError
from app.schemas.molecule_schema import PubChemCandidate
from app.services.connectivity_service import MolecularGraph, resolve_connectivity
from app.services.formula_parser import ParsedFormula

MIN_SUPPORTED_ATOMS = 3
MAX_SUPPORTED_ATOMS = 7


def ligand_symbols(atoms: dict[str, int], central: str) -> list[str]:
    """Every atom except the one acting as the centre.

    Homonuclear centres are ordinary: ozone is a central O with two O ligands, and
    triiodide is a central I with two I ligands. Removing exactly one atom of the
    central element -- rather than requiring the central element to appear once --
    is what lets those species through without a special case.
    """

    remaining = dict(atoms)
    if remaining.get(central, 0) < 1:
        raise ChemistryValidationError("The chosen central atom is not present in the formula.")
    remaining[central] -= 1
    return [symbol for symbol, count in remaining.items() for _ in range(count) if count > 0]


def validate_star_connectivity(graph: MolecularGraph, parsed: ParsedFormula, central: str) -> None:
    """Reject connectivity that is not the single-centre star this scope supports."""

    if dict(graph.inventory()) != parsed.atoms:
        raise ChemistryValidationError("Connectivity atom inventory does not match the formula.")
    if graph.fragment_count != 1:
        raise ChemistryValidationError("Only a single covalent unit is supported automatically.")
    if graph.single_center_id(central) is None:
        raise ChemistryValidationError("Connectivity is not a supported single-centre star graph.")


def solve_structure(
    parsed: ParsedFormula,
    *,
    graph: MolecularGraph | None = None,
    central_override: str | None = None,
) -> tuple[str, LewisSolution]:
    """Choose a centre and solve its Lewis structure, honouring validated connectivity."""

    atom_count = sum(parsed.atoms.values())
    if not MIN_SUPPORTED_ATOMS <= atom_count <= MAX_SUPPORTED_ATOMS:
        raise ChemistryValidationError(
            f"Automatic inference supports {MIN_SUPPORTED_ATOMS} to {MAX_SUPPORTED_ATOMS} atoms in one covalent unit."
        )
    central = central_override or choose_central_atom(parsed.atoms)
    if graph is not None:
        center_id = graph.single_center_id(central)
        if center_id is None:
            raise ChemistryValidationError("Connectivity is not a supported single-centre star graph.")
        central = next(atom.element for atom in graph.atoms if atom.id == center_id)
        ligands = [atom.element for atom in graph.atoms if atom.id != center_id]
    else:
        ligands = ligand_symbols(parsed.atoms, central)
    return central, solve_lewis(central, ligands, parsed.charge, atom_inventory=parsed.atoms)


def build_deterministic_record(parsed: ParsedFormula, candidate: PubChemCandidate | None = None) -> dict[str, Any]:
    """Return a record compatible with the Lewis/VSEPR services, or fail safely."""

    smiles = (candidate.canonical_smiles or candidate.isomeric_smiles) if candidate else None
    connectivity = resolve_connectivity(smiles=smiles)
    graph = connectivity.graph
    if graph is not None:
        central_guess = choose_central_atom(parsed.atoms)
        validate_star_connectivity(graph, parsed, central_guess)

    central, solution = solve_structure(parsed, graph=graph)
    structure = solution.representative
    rule = get_vsepr_rule(structure.bonding_domains, structure.center_lone_pairs)
    validate_formal_charge_sum(list(structure.formal_charges), parsed.charge)

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
        "atom_symbols": list(structure.atom_symbols),
        "central_atom": central,
        "total_valence_electrons": solution.total_valence_electrons,
        "bond_orders": list(structure.bond_orders),
        "lone_pairs": list(structure.lone_pairs),
        "formal_charges": list(structure.formal_charges),
        "resonance_forms": solution.resonance_forms,
        "resonance_note_vi": resonance_note(solution, "vi"),
        "resonance_note_en": resonance_note(solution, "en"),
        "exception_flags": {
            "electron_deficient": structure.electron_deficient,
            "expanded_octet": structure.expanded_octet,
            "odd_electron": False,
        },
        "bonding_domains": structure.bonding_domains,
        "lone_pair_domains": structure.center_lone_pairs,
        "steric_number": structure.steric_number,
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
        "polarity_note_en": "Polarity is not inferred automatically for an uncurated record.",
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
        "_connectivity_source": graph.source if graph else None,
    }
