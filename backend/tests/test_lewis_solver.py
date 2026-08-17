"""The general Lewis constraint solver, by chemical category rather than by species.

The point of these tests is that no case is served by a formula-specific branch: the
same rules produce water, ammonium, nitrate, sulfate and chlorine trifluoride. Where a
named species appears it is an *example* of its category, and the invariants asserted
around it (electron conservation, formal-charge balance, resonance counting) are
checked across the whole set.
"""

from __future__ import annotations

import pytest

from app.chemistry.central_atom_rules import choose_central_atom
from app.chemistry.lewis_solver import (
    MAX_EXPANDED_SHELL_ELECTRONS,
    LewisSolution,
    resonance_note,
    solve_lewis,
)
from app.chemistry.periodic_table import get_element
from app.chemistry.valence_rules import total_valence_electrons
from app.core.exceptions import ChemistryValidationError
from app.services.deterministic_chemistry_service import build_deterministic_record, ligand_symbols
from app.services.formula_parser import parse_formula


def solve(formula: str) -> LewisSolution:
    """Solve straight from a formula, exactly as the pipeline does."""

    parsed = parse_formula(formula)
    central = choose_central_atom(parsed.atoms)
    return solve_lewis(central, ligand_symbols(parsed.atoms, central), parsed.charge, atom_inventory=parsed.atoms)


#: One representative per chemical category the solver must handle.
CATEGORIES = [
    ("neutral ordinary molecule", "H2O", "AX2E2", [1, 1], 1),
    ("neutral ordinary molecule", "NH3", "AX3E", [1, 1, 1], 1),
    ("neutral ordinary molecule", "NF3", "AX3E", [1, 1, 1], 1),
    ("cation", "NH4+", "AX4", [1, 1, 1, 1], 1),
    ("cation", "H3O+", "AX3E", [1, 1, 1], 1),
    ("anion", "ClO4-", "AX4", [2, 2, 2, 1], 4),
    ("resonance oxoanion", "NO3-", "AX3", [2, 1, 1], 3),
    ("resonance oxoanion", "CO3^2-", "AX3", [2, 1, 1], 3),
    ("resonance oxoanion", "SO4^2-", "AX4", [2, 2, 1, 1], 6),
    ("neutral resonance species", "O3", "AX2E", [2, 1], 2),
    ("neutral non-resonant multiple bond", "SO2", "AX2E", [2, 2], 1),
    ("hypervalent central atom", "PCl5", "AX5", [1, 1, 1, 1, 1], 1),
    ("hypervalent central atom", "SF6", "AX6", [1, 1, 1, 1, 1, 1], 1),
    ("hypervalent central atom", "SF4", "AX4E", [1, 1, 1, 1], 1),
    ("one-angle geometry", "CH4", "AX4", [1, 1, 1, 1], 1),
    ("multiple-inequivalent-angle geometry", "ClF3", "AX3E2", [1, 1, 1], 1),
    ("multiple-inequivalent-angle geometry", "XeF4", "AX4E2", [1, 1, 1, 1], 1),
    ("electron-deficient centre", "BF3", "AX3", [1, 1, 1], 1),
]


@pytest.mark.parametrize(("category", "formula", "ax_en", "bond_orders", "resonance"), CATEGORIES)
def test_category_representatives_solve_correctly(
    category: str, formula: str, ax_en: str, bond_orders: list[int], resonance: int,
) -> None:
    solution = solve(formula)
    structure = solution.representative
    assert structure.ax_en == ax_en, category
    assert list(structure.bond_orders) == bond_orders, category
    assert solution.resonance_forms == resonance, category


@pytest.mark.parametrize("formula", [row[1] for row in CATEGORIES])
def test_electron_conservation_holds_for_every_category(formula: str) -> None:
    parsed = parse_formula(formula)
    solution = solve(formula)
    structure = solution.representative
    expected = total_valence_electrons(parsed.atoms, parsed.charge)
    represented = 2 * sum(structure.bond_orders) + 2 * sum(structure.lone_pairs)
    assert solution.total_valence_electrons == expected
    assert represented == expected


@pytest.mark.parametrize("formula", [row[1] for row in CATEGORIES])
def test_formal_charge_conservation_holds_for_every_category(formula: str) -> None:
    parsed = parse_formula(formula)
    structure = solve(formula).representative
    assert sum(structure.formal_charges) == parsed.charge


@pytest.mark.parametrize("formula", [row[1] for row in CATEGORIES])
def test_terminal_atoms_obey_the_duet_or_octet(formula: str) -> None:
    structure = solve(formula).representative
    for element, order, lone_pairs in zip(structure.ligands, structure.bond_orders, structure.ligand_lone_pairs, strict=True):
        shell = 2 * order + 2 * lone_pairs
        assert shell == (2 if element == "H" else 8), f"{formula}: {element}"


@pytest.mark.parametrize("formula", [row[1] for row in CATEGORIES])
def test_expanded_valence_is_controlled_and_never_used_by_period_2_centres(formula: str) -> None:
    structure = solve(formula).representative
    period = get_element(structure.center).period
    if period <= 2:
        assert structure.center_shell_electrons <= 8, f"{formula} expanded a period-2 octet"
    assert structure.center_shell_electrons <= MAX_EXPANDED_SHELL_ELECTRONS


@pytest.mark.parametrize("formula", [row[1] for row in CATEGORIES])
def test_every_solution_stays_inside_the_supported_vsepr_scope(formula: str) -> None:
    structure = solve(formula).representative
    assert 2 <= structure.steric_number <= 6
    assert structure.bonding_domains == len(structure.bond_orders)


# --------------------------------------------------------------------------- #
# The specific things the old engine could not do
# --------------------------------------------------------------------------- #


def test_terminal_oxygen_and_sulfur_no_longer_need_a_whitelist() -> None:
    """The old capability gate accepted only H and halogens as terminal atoms."""

    for formula in ("SO2", "NO3-", "CO3^2-", "SO4^2-", "ClO4-", "O3", "CO2", "SO3"):
        assert solve(formula).representative.bonding_domains >= 2


def test_multiple_bonds_are_generated_not_assumed_single() -> None:
    assert list(solve("CO2").representative.bond_orders) == [2, 2]
    assert list(solve("SO3").representative.bond_orders) == [2, 2, 2]
    assert list(solve("NO2-").representative.bond_orders) == [2, 1]


def test_sulfate_is_solved_by_the_general_rules_with_no_sulfate_specific_branch() -> None:
    """The mandated SO4^2- case: correct electrons, charge, resonance and AX4 geometry."""

    parsed = parse_formula("SO4^2-")
    solution = solve("SO4^2-")
    structure = solution.representative

    assert solution.total_valence_electrons == 32
    assert sum(structure.formal_charges) == -2 == parsed.charge
    assert list(structure.bond_orders) == [2, 2, 1, 1]
    assert list(structure.formal_charges) == [0, 0, 0, -1, -1]
    assert structure.ax_en == "AX4"
    assert solution.resonance_forms == 6  # choose(4, 2) equivalent placements
    assert structure.center_shell_electrons == 12

    record = build_deterministic_record(parsed)
    assert record["molecular_geometry"] == "tetrahedral"
    assert record["electron_geometry"] == "tetrahedral"
    assert record["resonance_forms"] == 6


def test_no_module_in_the_chemistry_layer_mentions_a_specific_formula() -> None:
    """Guards against re-introducing `if formula == "SO4^2-"`-style branches."""

    from pathlib import Path

    solver = Path(__file__).resolve().parents[1] / "app" / "chemistry" / "lewis_solver.py"
    source = solver.read_text(encoding="utf-8")
    body = "\n".join(
        line for line in source.splitlines()
        if not line.lstrip().startswith("#")
    )
    code = body.split('"""')[0] + '"""'.join(body.split('"""')[2::2])
    for formula in ("SO4", "NO3", "ClO4", "BF3", "XeF4", "PCl5"):
        assert formula not in code, f"{formula} appears in solver logic"


def test_boron_keeps_its_incomplete_octet_rather_than_separating_charge() -> None:
    """Formal charge outranks octet satisfaction, which is what BF3 requires."""

    structure = solve("BF3").representative
    assert list(structure.bond_orders) == [1, 1, 1]
    assert list(structure.formal_charges) == [0, 0, 0, 0]
    assert structure.electron_deficient
    assert structure.center_shell_electrons == 6


def test_negative_charge_is_placed_on_the_more_electronegative_atom() -> None:
    structure = solve("ClO4-").representative
    charges = dict(zip(structure.atom_symbols, structure.formal_charges, strict=True))
    assert charges["Cl"] == 0
    assert min(structure.formal_charges) == -1
    negative_index = structure.formal_charges.index(-1)
    assert structure.atom_symbols[negative_index] == "O"


def test_homonuclear_centres_are_ordinary_not_special_cases() -> None:
    """Ozone's centre is the same element as its ligands."""

    solution = solve("O3")
    assert solution.representative.center == "O"
    assert solution.representative.ligands == ("O", "O")
    assert solution.resonance_forms == 2


# --------------------------------------------------------------------------- #
# Resonance
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(("formula", "forms"), [
    ("NO3-", 3), ("CO3^2-", 3), ("SO4^2-", 6), ("ClO4-", 4), ("O3", 2), ("NO2-", 2),
    ("H2O", 1), ("CH4", 1), ("SF6", 1), ("CO2", 1),
])
def test_resonance_enumeration_counts_equivalent_forms(formula: str, forms: int) -> None:
    solution = solve(formula)
    assert solution.resonance_forms == forms
    assert len(solution.equivalent) == forms
    assert solution.has_resonance == (forms > 1)


def test_equivalent_forms_share_one_canonical_signature() -> None:
    solution = solve("SO4^2-")
    signatures = {candidate.signature() for candidate in solution.equivalent}
    assert len(signatures) == 1, "equivalent forms must canonicalize to one signature"


def test_resonance_notes_are_bilingual_and_count_driven() -> None:
    solution = solve("NO3-")
    assert "3" in (resonance_note(solution, "vi") or "")
    assert "3 equivalent" in (resonance_note(solution, "en") or "")
    assert resonance_note(solve("CH4"), "en") is None


# --------------------------------------------------------------------------- #
# Refusals
# --------------------------------------------------------------------------- #


def test_open_shell_species_are_refused_rather_than_guessed() -> None:
    with pytest.raises(ChemistryValidationError, match="odd number of valence electrons"):
        solve("NO2")


def test_hydrogen_cannot_be_the_central_atom() -> None:
    with pytest.raises(ChemistryValidationError):
        solve_lewis("H", ["H"], 0)


def test_a_composition_with_no_valid_structure_is_refused() -> None:
    with pytest.raises(ChemistryValidationError):
        solve_lewis("Ne", ["F", "F", "F", "F", "F", "F"], 0)


def test_steric_numbers_beyond_the_supported_table_are_refused() -> None:
    with pytest.raises(ChemistryValidationError):
        solve_lewis("S", ["F"] * 7, 0)
