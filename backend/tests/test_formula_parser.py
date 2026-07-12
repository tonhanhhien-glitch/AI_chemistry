"""Regression tests for the strict formula parser."""

import pytest

from app.core.exceptions import FormulaParseError, UnsupportedElementError
from app.services.formula_parser import parse_formula


@pytest.mark.parametrize(
    ("formula", "atoms", "charge"),
    [
        ("H2O", {"H": 2, "O": 1}, 0),
        ("NH3", {"N": 1, "H": 3}, 0),
        ("CO2", {"C": 1, "O": 2}, 0),
        ("NaCl", {"Na": 1, "Cl": 1}, 0),
        ("Cl2", {"Cl": 2}, 0),
        ("MgCl2", {"Mg": 1, "Cl": 2}, 0),
        ("Al2O3", {"Al": 2, "O": 3}, 0),
        ("SiO2", {"Si": 1, "O": 2}, 0),
        ("Br2", {"Br": 2}, 0),
        ("XeF4", {"Xe": 1, "F": 4}, 0),
        ("NH4+", {"N": 1, "H": 4}, 1),
        ("NO3-", {"N": 1, "O": 3}, -1),
        ("SO4^2-", {"S": 1, "O": 4}, -2),
        ("CH3COOH", {"C": 2, "H": 4, "O": 2}, 0),
    ],
)
def test_parse_valid_formula(
    formula: str, atoms: dict[str, int], charge: int
) -> None:
    result = parse_formula(formula)

    assert result.formula == formula
    assert result.atoms == atoms
    assert result.charge == charge


@pytest.mark.parametrize(
    "symbol",
    ["He", "Li", "Be", "Ne", "Na", "Mg", "Al", "Si", "Cl", "Ar", "Ca", "Br", "Xe"],
)
def test_every_supported_two_letter_symbol_is_preserved(symbol: str) -> None:
    result = parse_formula(f"{symbol}2")

    assert result.atoms == {symbol: 2}


@pytest.mark.parametrize(
    "formula",
    [
        "",
        "   ",
        "2H",
        "H0",
        "H02",
        "H2O$",
        "H2Oabc",
        "SO4++",
        "SO4^",
        "SO4^2",
        "+",
        "Ca(OH)2",
        "nacl",
    ],
)
def test_reject_invalid_formula(formula: str) -> None:
    with pytest.raises(FormulaParseError):
        parse_formula(formula)


def test_reject_unsupported_element() -> None:
    with pytest.raises(UnsupportedElementError) as exc_info:
        parse_formula("FeCl3")

    assert exc_info.value.code == "UNSUPPORTED_ELEMENT"
