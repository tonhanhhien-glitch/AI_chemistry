"""Unit coverage for deterministic chemistry source-of-truth modules."""

import pytest

from app.chemistry.central_atom_rules import choose_central_atom
from app.chemistry.formal_charge import calculate_formal_charge, validate_formal_charge_sum
from app.chemistry.hybridization import pedagogical_hybridization
from app.chemistry.octet_exceptions import classify_octet_exception
from app.chemistry.periodic_table import get_element
from app.chemistry.valence_rules import total_valence_electrons
from app.chemistry.vsepr_rules import VSEPR_RULES, get_vsepr_rule
from app.core.exceptions import ChemistryValidationError, InvalidAtomCountError, UnknownElementError


def test_periodic_table_raises_domain_error() -> None:
    with pytest.raises(UnknownElementError):
        get_element("Fe")


@pytest.mark.parametrize(("atoms", "charge", "total"), [({"N": 1, "H": 4}, 1, 8), ({"N": 1, "O": 3}, -1, 24), ({"C": 1, "O": 3}, -2, 24)])
def test_total_valence_with_ionic_adjustment(atoms: dict[str, int], charge: int, total: int) -> None:
    assert total_valence_electrons(atoms, charge) == total


def test_total_valence_rejects_bad_counts() -> None:
    with pytest.raises(InvalidAtomCountError):
        total_valence_electrons({"O": 0})


def test_central_atom_allows_interhalogens() -> None:
    assert choose_central_atom({"Cl": 1, "F": 3}) == "Cl"
    assert choose_central_atom({"Br": 1, "F": 5}) == "Br"


def test_central_atom_rejects_h_and_f_override() -> None:
    with pytest.raises(ChemistryValidationError):
        choose_central_atom({"H": 2, "O": 1}, "H")


def test_formal_charge_formula_and_sum() -> None:
    assert calculate_formal_charge("N", 0, 8) == 1
    validate_formal_charge_sum([1, 0, 0, 0, 0], 1)
    with pytest.raises(ChemistryValidationError):
        validate_formal_charge_sum([1, -1], 1)


def test_octet_exceptions() -> None:
    assert classify_octet_exception(central_electrons=6, total_valence=24, central_period=2).electron_deficient
    assert classify_octet_exception(central_electrons=12, total_valence=48, central_period=3).expanded_octet
    assert classify_octet_exception(central_electrons=7, total_valence=17, central_period=2).odd_electron


def test_complete_vsepr_contract() -> None:
    expected = {"AX2", "AX3", "AX2E", "AX4", "AX3E", "AX2E2", "AX5", "AX4E", "AX3E2", "AX2E3", "AX6", "AX5E", "AX4E2"}
    assert set(VSEPR_RULES) == expected
    assert get_vsepr_rule(3, 2).molecular_geometry == "T-shaped"
    label, warning = pedagogical_hybridization(6)
    assert label == "sp³d²"
    assert "gần đúng" in warning
