"""Strict parser for flat, main-group chemical formulas and simple ions."""

from dataclasses import dataclass
import re

from app.chemistry.periodic_table import SUPPORTED_ELEMENTS
from app.core.exceptions import (
    FormulaParseError,
    UnsupportedElementError,
    UnsupportedFormulaSyntaxError,
)

_TOKEN_PATTERN = re.compile(r"([A-Z][a-z]?)([1-9]\d*)?")
_FORMULA_BODY_PATTERN = re.compile(r"(?:[A-Z][a-z]?(?:[1-9]\d*)?)+")
_EXPLICIT_CHARGE_PATTERN = re.compile(r"\^([1-9]\d*)([+-])$")


@dataclass(frozen=True)
class ParsedFormula:
    formula: str
    atoms: dict[str, int]
    charge: int


def _extract_charge(formula: str) -> tuple[str, int]:
    explicit_charge = _EXPLICIT_CHARGE_PATTERN.search(formula)
    if explicit_charge:
        magnitude = int(explicit_charge.group(1))
        sign = 1 if explicit_charge.group(2) == "+" else -1
        return formula[: explicit_charge.start()], sign * magnitude

    if formula.endswith(("+", "-")):
        sign = 1 if formula[-1] == "+" else -1
        return formula[:-1], sign

    return formula, 0


def format_charge_suffix(charge: int) -> str:
    """Render a charge in this application's grammar: ``+``, ``-``, ``^2-``."""

    if charge == 0:
        return ""
    sign = "+" if charge > 0 else "-"
    return sign if abs(charge) == 1 else f"^{abs(charge)}{sign}"


def canonical_formula(atoms: dict[str, int], charge: int = 0) -> str:
    """Render an atom inventory in this application's conventional order.

    External sources use Hill notation, so PubChem calls sulfate ``O4S`` while the
    teaching convention -- and every curated record here -- writes ``SO4^2-``. Rendering
    from the inventory rather than passing a source's string through keeps one canonical
    spelling, so identities are compared on composition instead of on formatting.

    The central atom leads, and the remaining elements follow alphabetically. When no
    central atom can be chosen the elements are simply alphabetical.
    """

    from app.chemistry.central_atom_rules import choose_central_atom
    from app.core.exceptions import ChemistryDomainError

    try:
        central: str | None = choose_central_atom(atoms)
    except ChemistryDomainError:
        central = None
    ordered = sorted(atoms)
    if central is not None and central in ordered:
        ordered = [central, *(symbol for symbol in ordered if symbol != central)]
    body = "".join(f"{symbol}{atoms[symbol] if atoms[symbol] > 1 else ''}" for symbol in ordered)
    return f"{body}{format_charge_suffix(charge)}"


def parse_formula(formula: str) -> ParsedFormula:
    """Parse a formula only when every character matches the supported grammar."""

    if not isinstance(formula, str):
        raise FormulaParseError()

    normalized_formula = formula.strip()
    if not normalized_formula:
        raise FormulaParseError("Chemical formula cannot be empty.")

    body, charge = _extract_charge(normalized_formula)
    if not body:
        raise UnsupportedFormulaSyntaxError()

    if not _FORMULA_BODY_PATTERN.fullmatch(body):
        raise UnsupportedFormulaSyntaxError()

    atoms: dict[str, int] = {}
    position = 0
    for match in _TOKEN_PATTERN.finditer(body):
        if match.start() != position:
            raise UnsupportedFormulaSyntaxError()

        element, count_text = match.groups()
        if element not in SUPPORTED_ELEMENTS:
            raise UnsupportedElementError(element)

        count = int(count_text) if count_text else 1
        atoms[element] = atoms.get(element, 0) + count
        position = match.end()

    if position != len(body) or not atoms:
        raise UnsupportedFormulaSyntaxError()

    return ParsedFormula(formula=normalized_formula, atoms=atoms, charge=charge)
