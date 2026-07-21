"""Deterministic valence-electron accounting."""

from collections.abc import Mapping

from app.chemistry.periodic_table import get_valence_electrons
from app.core.exceptions import InvalidAtomCountError


def total_valence_electrons(atoms: Mapping[str, int], charge: int = 0) -> int:
    """Return neutral valence sum minus ionic charge."""

    if isinstance(charge, bool) or not isinstance(charge, int):
        raise ValueError("charge must be an integer")
    total = 0
    for symbol, count in atoms.items():
        if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
            raise InvalidAtomCountError(symbol, count)
        total += get_valence_electrons(symbol) * count
    return total - charge
