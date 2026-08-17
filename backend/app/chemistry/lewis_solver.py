"""A general Lewis-structure constraint solver for the single-centre main-group domain.

This replaces the old ``_TERMINAL_SINGLE_BOND`` whitelist, which decided what the
application could analyse by listing the terminal elements it happened to trust and
assuming every bond was single. Nothing here is keyed on a formula, an element
whitelist or a species name: candidate structures are *generated* by enumerating
central-ligand bond orders, filtered by hard chemical constraints, and ranked by
chemically meaningful criteria.

Hard constraints every candidate must satisfy
---------------------------------------------
* exact total valence-electron conservation,
* total formal charge equal to the requested molecular/ionic charge,
* the hydrogen duet,
* the octet rule for period-2 centres and for terminal atoms,
* controlled expanded valence for centres from period 3 onwards,
* bond orders in 1..3 and non-negative lone-pair counts,
* a central-atom electron-domain count inside the supported VSEPR table.

Ranking, lexicographically (lower is better)
--------------------------------------------
1. total magnitude of formal charges,
2. octet satisfaction at the centre,
3. charge separation across the structure,
4. placement of negative charge on the more electronegative atoms,
5. controlled use of expanded valence.

Formal charge is ranked ahead of octet satisfaction on purpose: BF3's accepted
teaching structure has an incomplete octet on boron precisely because the
octet-completing alternative would separate charge.

Resonance is a first-class result. Every assignment tied at the best score is kept,
equivalent forms are canonicalised, and the count is reported.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from app.chemistry.formal_charge import calculate_formal_charge
from app.chemistry.periodic_table import get_element
from app.chemistry.valence_rules import total_valence_electrons
from app.chemistry.vsepr_rules import VSEPR_RULES, ax_notation
from app.core.exceptions import ChemistryValidationError

#: Electrons a period-3+ centre may hold. ClO4- needs 14 at its best-scoring form;
#: 16 is the ceiling implied by eight electron pairs around one centre.
MAX_EXPANDED_SHELL_ELECTRONS = 16
MAX_BOND_ORDER = 3
_OCTET = 8
_DUET = 2


@dataclass(frozen=True, slots=True)
class LewisCandidate:
    """One complete electron assignment over a single-centre star framework."""

    center: str
    ligands: tuple[str, ...]
    bond_orders: tuple[int, ...]
    center_lone_pairs: int
    ligand_lone_pairs: tuple[int, ...]
    formal_charges: tuple[int, ...]
    center_shell_electrons: int

    @property
    def bonding_domains(self) -> int:
        return len(self.ligands)

    @property
    def steric_number(self) -> int:
        return self.bonding_domains + self.center_lone_pairs

    @property
    def ax_en(self) -> str:
        return ax_notation(self.bonding_domains, self.center_lone_pairs)

    @property
    def atom_symbols(self) -> tuple[str, ...]:
        return (self.center, *self.ligands)

    @property
    def lone_pairs(self) -> tuple[int, ...]:
        return (self.center_lone_pairs, *self.ligand_lone_pairs)

    @property
    def electron_deficient(self) -> bool:
        return self.center_shell_electrons < _OCTET

    @property
    def expanded_octet(self) -> bool:
        return self.center_shell_electrons > _OCTET

    def signature(self) -> tuple[tuple[str, int, int, int], ...]:
        """Canonical, order-independent identity used to recognise equivalent forms."""

        return tuple(sorted(
            (element, order, lone_pairs, charge)
            for element, order, lone_pairs, charge in zip(
                self.ligands, self.bond_orders, self.ligand_lone_pairs, self.formal_charges[1:], strict=True,
            )
        ))


@dataclass(frozen=True, slots=True)
class LewisSolution:
    """The winning structure plus every equivalent form tied with it."""

    representative: LewisCandidate
    resonance_forms: int
    equivalent: tuple[LewisCandidate, ...]
    total_valence_electrons: int
    score: tuple[float, ...]

    @property
    def has_resonance(self) -> bool:
        return self.resonance_forms > 1


def _terminal_lone_pairs(element: str, order: int) -> int | None:
    """Lone pairs completing a terminal atom's shell, or ``None`` when impossible."""

    if element == "H":
        return 0 if order == 1 else None
    remaining = _OCTET - 2 * order
    return remaining // 2 if remaining >= 0 else None


def _terminal_shell(element: str, order: int, lone_pairs: int) -> int:
    return 2 * order + 2 * lone_pairs if element != "H" else 2 * order


def _electronegativity(symbol: str) -> float:
    value = get_element(symbol).electronegativity
    return 0.0 if value is None else value


def _score(candidate: LewisCandidate) -> tuple[float, ...]:
    charges = candidate.formal_charges
    symbols = candidate.atom_symbols
    total_magnitude = sum(abs(charge) for charge in charges)
    octet_penalty = 1 if candidate.electron_deficient else 0
    separation = max(charges) - min(charges)
    # Negative formal charge belongs on the more electronegative atoms, so the more
    # negative this sum is, the better the placement.
    placement = sum(charge * _electronegativity(symbol) for charge, symbol in zip(charges, symbols, strict=True))
    expansion = max(0, (candidate.center_shell_electrons - _OCTET) // 2)
    return (total_magnitude, octet_penalty, separation, placement, expansion)


def _candidate(
    center: str,
    ligands: tuple[str, ...],
    orders: tuple[int, ...],
    total: int,
    charge: int,
    center_period: int,
) -> LewisCandidate | None:
    """Complete one bond-order assignment into a candidate, or reject it."""

    ligand_lone_pairs: list[int] = []
    for element, order in zip(ligands, orders, strict=True):
        lone_pairs = _terminal_lone_pairs(element, order)
        if lone_pairs is None:
            return None
        if _terminal_shell(element, order, lone_pairs) not in {_DUET if element == "H" else _OCTET}:
            return None
        ligand_lone_pairs.append(lone_pairs)

    bonding_electrons = 2 * sum(orders)
    remaining = total - bonding_electrons - 2 * sum(ligand_lone_pairs)
    if remaining < 0 or remaining % 2:
        return None
    center_lone_pairs = remaining // 2
    center_shell = bonding_electrons + 2 * center_lone_pairs
    if center_period <= 2 and center_shell > _OCTET:
        return None
    if center_shell > MAX_EXPANDED_SHELL_ELECTRONS:
        return None
    if ax_notation(len(ligands), center_lone_pairs) not in VSEPR_RULES:
        return None

    charges = [calculate_formal_charge(center, 2 * center_lone_pairs, bonding_electrons)]
    charges.extend(
        calculate_formal_charge(element, 2 * lone_pairs, 2 * order)
        for element, order, lone_pairs in zip(ligands, orders, ligand_lone_pairs, strict=True)
    )
    if sum(charges) != charge:
        return None
    return LewisCandidate(
        center=center, ligands=ligands, bond_orders=orders,
        center_lone_pairs=center_lone_pairs, ligand_lone_pairs=tuple(ligand_lone_pairs),
        formal_charges=tuple(charges), center_shell_electrons=center_shell,
    )


def _canonical(candidate: LewisCandidate) -> LewisCandidate:
    """Order ligand slots deterministically: element groups in first-seen order, highest bond order first."""

    element_order: list[str] = []
    for element in candidate.ligands:
        if element not in element_order:
            element_order.append(element)
    slots = sorted(
        zip(candidate.ligands, candidate.bond_orders, candidate.ligand_lone_pairs, candidate.formal_charges[1:], strict=True),
        key=lambda slot: (element_order.index(slot[0]), -slot[1]),
    )
    return LewisCandidate(
        center=candidate.center,
        ligands=tuple(slot[0] for slot in slots),
        bond_orders=tuple(slot[1] for slot in slots),
        center_lone_pairs=candidate.center_lone_pairs,
        ligand_lone_pairs=tuple(slot[2] for slot in slots),
        formal_charges=(candidate.formal_charges[0], *(slot[3] for slot in slots)),
        center_shell_electrons=candidate.center_shell_electrons,
    )


def solve_lewis(
    center: str,
    ligands: list[str] | tuple[str, ...],
    charge: int,
    *,
    atom_inventory: dict[str, int] | None = None,
) -> LewisSolution:
    """Solve the Lewis structure for a single-centre star framework.

    Raises :class:`ChemistryValidationError` when no candidate satisfies every hard
    constraint, which is how species outside the supported domain are refused rather
    than guessed at.
    """

    ligands = tuple(ligands)
    if not ligands:
        raise ChemistryValidationError("A Lewis structure needs at least one ligand around the central atom.")
    if center in {"H"}:
        raise ChemistryValidationError("Hydrogen cannot be the central atom within this scope.")
    inventory = dict(atom_inventory) if atom_inventory else None
    if inventory is None:
        inventory = {}
        for symbol in (center, *ligands):
            inventory[symbol] = inventory.get(symbol, 0) + 1

    total = total_valence_electrons(inventory, charge)
    if total % 2:
        raise ChemistryValidationError(
            "The species has an odd number of valence electrons; open-shell chemistry is outside this scope."
        )
    center_period = get_element(center).period

    ranges = [
        range(1, 2) if element == "H" else range(1, MAX_BOND_ORDER + 1)
        for element in ligands
    ]
    best_score: tuple[float, ...] | None = None
    winners: list[LewisCandidate] = []
    for orders in product(*ranges):
        candidate = _candidate(center, ligands, tuple(orders), total, charge, center_period)
        if candidate is None:
            continue
        score = _score(candidate)
        if best_score is None or score < best_score:
            best_score, winners = score, [candidate]
        elif score == best_score:
            winners.append(candidate)

    if best_score is None or not winners:
        raise ChemistryValidationError(
            "No Lewis structure satisfies electron conservation, formal-charge balance and the "
            "octet/expanded-valence rules for this composition."
        )
    representative = _canonical(winners[0])
    return LewisSolution(
        representative=representative,
        resonance_forms=len(winners),
        equivalent=tuple(_canonical(candidate) for candidate in winners),
        total_valence_electrons=total,
        score=best_score,
    )


def resonance_note(solution: LewisSolution, language: str = "vi") -> str | None:
    """Bilingual, count-driven resonance note; ``None`` for a single structure."""

    if not solution.has_resonance:
        return None
    count = solution.resonance_forms
    if language == "en":
        return (
            f"{count} equivalent Lewis structures differ only in where the multiple bonds sit, "
            "so the real electron distribution is the delocalised average of them."
        )
    return (
        f"Có {count} công thức Lewis tương đương chỉ khác nhau ở vị trí liên kết bội, "
        "nên phân bố electron thực tế là trung bình cộng hưởng của chúng."
    )
