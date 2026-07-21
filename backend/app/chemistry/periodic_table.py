"""Single validated registry for elements supported by the MVP."""

from dataclasses import dataclass

from app.core.exceptions import UnknownElementError


@dataclass(frozen=True, slots=True)
class Element:
    symbol: str
    name: str
    atomic_number: int
    group: int
    period: int
    valence_electrons: int
    electronegativity: float | None
    supported: bool = True


_RAW_ELEMENTS = (
    ("H", "Hydrogen", 1, 1, 1, 1, 2.20),
    ("He", "Helium", 2, 18, 1, 2, None),
    ("Li", "Lithium", 3, 1, 2, 1, 0.98),
    ("Be", "Beryllium", 4, 2, 2, 2, 1.57),
    ("B", "Boron", 5, 13, 2, 3, 2.04),
    ("C", "Carbon", 6, 14, 2, 4, 2.55),
    ("N", "Nitrogen", 7, 15, 2, 5, 3.04),
    ("O", "Oxygen", 8, 16, 2, 6, 3.44),
    ("F", "Fluorine", 9, 17, 2, 7, 3.98),
    ("Ne", "Neon", 10, 18, 2, 8, None),
    ("Na", "Sodium", 11, 1, 3, 1, 0.93),
    ("Mg", "Magnesium", 12, 2, 3, 2, 1.31),
    ("Al", "Aluminium", 13, 13, 3, 3, 1.61),
    ("Si", "Silicon", 14, 14, 3, 4, 1.90),
    ("P", "Phosphorus", 15, 15, 3, 5, 2.19),
    ("S", "Sulfur", 16, 16, 3, 6, 2.58),
    ("Cl", "Chlorine", 17, 17, 3, 7, 3.16),
    ("Ar", "Argon", 18, 18, 3, 8, None),
    ("K", "Potassium", 19, 1, 4, 1, 0.82),
    ("Ca", "Calcium", 20, 2, 4, 2, 1.00),
    ("Br", "Bromine", 35, 17, 4, 7, 2.96),
    ("I", "Iodine", 53, 17, 5, 7, 2.66),
    ("Xe", "Xenon", 54, 18, 5, 8, 2.60),
)

ELEMENTS: dict[str, Element] = {row[0]: Element(*row) for row in _RAW_ELEMENTS}
SUPPORTED_ELEMENTS = frozenset(ELEMENTS)


def get_element(symbol: str) -> Element:
    """Return an element or raise a stable domain error."""

    try:
        return ELEMENTS[symbol]
    except KeyError as exc:
        raise UnknownElementError(symbol) from exc


def get_valence_electrons(symbol: str) -> int:
    return get_element(symbol).valence_electrons
