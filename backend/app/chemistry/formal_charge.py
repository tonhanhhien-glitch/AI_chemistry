"""Formal-charge calculation and molecular consistency checks."""

from collections.abc import Iterable, Mapping

from app.chemistry.periodic_table import get_valence_electrons
from app.core.exceptions import ChemistryValidationError


def calculate_formal_charge(symbol: str, nonbonding_electrons: int, bonding_electrons: int) -> int:
    """Calculate FC = V - (nonbonding + bonding / 2)."""

    values = (nonbonding_electrons, bonding_electrons)
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in values
    ):
        raise ChemistryValidationError(
            "Số electron liên kết và không liên kết phải là số nguyên không âm."
        )
    if bonding_electrons % 2:
        raise ChemistryValidationError("Số electron liên kết phải là số chẵn.")
    return (
        get_valence_electrons(symbol)
        - nonbonding_electrons
        - bonding_electrons // 2
    )


def validate_formal_charge_sum(
    charges: Mapping[str, int] | Iterable[int], molecular_charge: int
) -> None:
    values = charges.values() if isinstance(charges, Mapping) else charges
    if sum(values) != molecular_charge:
        raise ChemistryValidationError(
            "Tổng điện tích hình thức không bằng điện tích toàn phần."
        )
