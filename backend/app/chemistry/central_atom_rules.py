"""Central-atom selection: curated override, then a conservative heuristic."""

from collections.abc import Mapping

from app.chemistry.periodic_table import get_element
from app.core.exceptions import ChemistryValidationError


def choose_central_atom(atoms: Mapping[str, int], curated_override: str | None = None) -> str:
    """Choose a plausible center; connectivity still needs validated structure data."""

    if curated_override:
        if curated_override not in atoms:
            raise ChemistryValidationError("The central atom is not present in the formula.")
        if curated_override in {"H", "F"}:
            raise ChemistryValidationError("H and F cannot be the central atom within this scope.")
        return curated_override
    candidates = [symbol for symbol in atoms if symbol not in {"H", "F"}]
    if not candidates:
        raise ChemistryValidationError("Could not determine the central atom.")
    unique = [symbol for symbol in candidates if atoms[symbol] == 1]
    pool = unique or candidates
    return min(
        pool,
        key=lambda symbol: (
            get_element(symbol).electronegativity
            if get_element(symbol).electronegativity is not None
            else 99.0,
            get_element(symbol).atomic_number,
        ),
    )
