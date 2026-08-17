"""One connectivity abstraction, built by real parsers instead of a regex mini-SMILES.

The old ``_simple_smiles_graph`` grew a hand-written token regex that understood a
shrinking subset of SMILES and rejected everything else, which made connectivity a
capability gate. Connectivity now comes from established parsers:

* RDKit, when ``ENABLE_RDKIT`` is set -- full SMILES including bracket atoms,
  formal charges, branches, bond orders and rings;
* a V2000 molfile / SDF block, which is the connectivity representation PubChem
  actually publishes (atom block, bond block and ``M  CHG`` charge lines).

Neither parser is allowed to decide chemistry. A :class:`MolecularGraph` is a
statement about *which atoms are bonded*; valence-electron accounting, Lewis
structures, formal charges, resonance, electron domains and VSEPR stay with the
deterministic layer.
"""

from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from app.services.formula_parser import ParsedFormula

from app.core.config import settings
from app.schemas.molecule_schema import ExternalServiceState, ExternalServiceStatus

logger = logging.getLogger(__name__)

ConnectivitySource = Literal["rdkit_smiles", "molfile", "curated_record"]


class TopologyResolutionStatus(StrEnum):
    VALIDATED = "validated"
    UNIQUE_FORMULA_TOPOLOGY = "unique_formula_topology"
    AMBIGUOUS = "ambiguous"
    UNSUPPORTED = "unsupported"
    EXTERNAL_LOOKUP_FAILED = "external_lookup_failed"


@dataclass(frozen=True, slots=True)
class GraphAtom:
    id: str
    element: str
    formal_charge: int = 0
    x: float | None = None
    y: float | None = None
    z: float | None = None

    @property
    def has_coordinates(self) -> bool:
        return self.x is not None and self.y is not None and self.z is not None


@dataclass(frozen=True, slots=True)
class GraphBond:
    atom1_id: str
    atom2_id: str
    order: int = 1


@dataclass(frozen=True, slots=True)
class MolecularGraph:
    atoms: tuple[GraphAtom, ...]
    bonds: tuple[GraphBond, ...]
    source: ConnectivitySource
    total_charge: int = 0
    fragment_count: int = 1
    coordinate_dimension: int = 0

    def inventory(self) -> Counter[str]:
        return Counter(atom.element for atom in self.atoms)

    def degree(self, atom_id: str) -> int:
        return sum(1 for bond in self.bonds if atom_id in (bond.atom1_id, bond.atom2_id))

    def neighbors(self, atom_id: str) -> list[str]:
        return [
            bond.atom2_id if bond.atom1_id == atom_id else bond.atom1_id
            for bond in self.bonds
            if atom_id in (bond.atom1_id, bond.atom2_id)
        ]

    def bond_order(self, first_id: str, second_id: str) -> int | None:
        for bond in self.bonds:
            if {bond.atom1_id, bond.atom2_id} == {first_id, second_id}:
                return bond.order
        return None

    @property
    def has_coordinates(self) -> bool:
        return bool(self.atoms) and all(atom.has_coordinates for atom in self.atoms)

    def single_center_id(self, central_element: str | None = None) -> str | None:
        """Return the hub id when the graph is a star, otherwise ``None``.

        A star graph -- one centre bonded to every other atom, with no other bonds --
        is the topology the single-central-atom VSEPR domain covers. This checks the
        shape; it does not assume anything about bond orders.
        """

        if len(self.atoms) < 3 or len(self.bonds) != len(self.atoms) - 1:
            return None
        candidates = [
            atom for atom in self.atoms
            if self.degree(atom.id) == len(self.atoms) - 1
            and (central_element is None or atom.element == central_element)
        ]
        if len(candidates) != 1:
            return None
        center = candidates[0]
        if any(self.degree(atom.id) != 1 for atom in self.atoms if atom.id != center.id):
            return None
        return center.id


@dataclass(frozen=True, slots=True)
class ConnectivityResult:
    graph: MolecularGraph | None
    status: ExternalServiceStatus
    statuses: tuple[ExternalServiceStatus, ...] = field(default=())


def _status(service: str, state: ExternalServiceState, message: str | None = None) -> ExternalServiceStatus:
    return ExternalServiceStatus(service=service, state=state, message=message)


# --------------------------------------------------------------------------- #
# V2000 molfile / SDF
# --------------------------------------------------------------------------- #


def parse_molfile(data: str) -> MolecularGraph | None:
    """Parse a V2000 molfile/SDF connectivity block, including ``M  CHG`` charges.

    V2000 is column-positional in principle, but PubChem and RDKit both emit
    whitespace-aligned blocks, so splitting on whitespace is both simpler and more
    tolerant here. Returns ``None`` for anything that is not a well-formed block.
    """

    lines = data.splitlines()
    counts_index = next((index for index, line in enumerate(lines) if "V2000" in line), None)
    if counts_index is None:
        return None
    try:
        counts = lines[counts_index].split()
        atom_count, bond_count = int(counts[0]), int(counts[1])
        if atom_count <= 0:
            return None
        atom_lines = lines[counts_index + 1 : counts_index + 1 + atom_count]
        bond_lines = lines[counts_index + 1 + atom_count : counts_index + 1 + atom_count + bond_count]
        if len(atom_lines) != atom_count or len(bond_lines) != bond_count:
            return None
        positions: list[tuple[float, float, float]] = []
        elements: list[str] = []
        for line in atom_lines:
            parts = line.split()
            positions.append((float(parts[0]), float(parts[1]), float(parts[2])))
            elements.append(parts[3])
        bonds: list[GraphBond] = []
        for line in bond_lines:
            parts = line.split()
            first, second, order = int(parts[0]) - 1, int(parts[1]) - 1, int(parts[2])
            if not (0 <= first < atom_count and 0 <= second < atom_count) or not 1 <= order <= 3:
                return None
            bonds.append(GraphBond(atom1_id=f"a{first}", atom2_id=f"a{second}", order=order))
    except (IndexError, TypeError, ValueError):
        return None

    charges = dict.fromkeys(range(atom_count), 0)
    for line in lines[counts_index + 1 + atom_count + bond_count :]:
        if not line.startswith("M  CHG"):
            continue
        parts = line.split()
        try:
            pairs = int(parts[2])
            for index in range(pairs):
                atom_index = int(parts[3 + 2 * index]) - 1
                value = int(parts[4 + 2 * index])
                if 0 <= atom_index < atom_count:
                    charges[atom_index] = value
        except (IndexError, ValueError):
            continue

    atoms = tuple(
        GraphAtom(
            id=f"a{index}", element=elements[index], formal_charge=charges[index],
            x=positions[index][0], y=positions[index][1], z=positions[index][2],
        )
        for index in range(atom_count)
    )
    dimension = 3 if any(abs(point[2]) > 1e-9 for point in positions) else 2
    graph = MolecularGraph(
        atoms=atoms, bonds=tuple(bonds), source="molfile",
        total_charge=sum(charges.values()),
        fragment_count=_fragment_count(atoms, tuple(bonds)),
        coordinate_dimension=dimension,
    )
    return graph


def _fragment_count(atoms: tuple[GraphAtom, ...], bonds: tuple[GraphBond, ...]) -> int:
    """Connected components, so a salt or a hydrate can be rejected explicitly."""

    parent = {atom.id: atom.id for atom in atoms}

    def find(node: str) -> str:
        while parent[node] != node:
            parent[node] = parent[parent[node]]
            node = parent[node]
        return node

    for bond in bonds:
        first, second = find(bond.atom1_id), find(bond.atom2_id)
        if first != second:
            parent[first] = second
    return len({find(atom.id) for atom in atoms})


# --------------------------------------------------------------------------- #
# RDKit SMILES
# --------------------------------------------------------------------------- #


def parse_smiles(smiles: str) -> MolecularGraph | None:
    """Parse SMILES with RDKit. Returns ``None`` when RDKit is unavailable or the input is invalid.

    Bracket atoms, explicit formal charges, branches, ring closures and bond orders
    are all handled by RDKit; this project deliberately does not maintain its own
    SMILES grammar.
    """

    try:
        from rdkit import Chem
        from rdkit import RDLogger
    except ImportError:
        return None
    RDLogger.DisableLog("rdApp.*")
    try:
        base = Chem.MolFromSmiles(smiles)
        if base is None:
            return None
        molecule = Chem.AddHs(base)
    except (RuntimeError, ValueError):
        return None
    atoms = tuple(
        GraphAtom(id=f"a{atom.GetIdx()}", element=atom.GetSymbol(), formal_charge=atom.GetFormalCharge())
        for atom in molecule.GetAtoms()
    )
    order_of = {1.0: 1, 2.0: 2, 3.0: 3, 1.5: 1}
    bonds = tuple(
        GraphBond(
            atom1_id=f"a{bond.GetBeginAtomIdx()}", atom2_id=f"a{bond.GetEndAtomIdx()}",
            order=order_of.get(float(bond.GetBondTypeAsDouble()), 1),
        )
        for bond in molecule.GetBonds()
    )
    return MolecularGraph(
        atoms=atoms, bonds=bonds, source="rdkit_smiles",
        total_charge=sum(atom.formal_charge for atom in atoms),
        fragment_count=_fragment_count(atoms, bonds),
    )


def check_formula_topology_eligibility(
    parsed: "ParsedFormula",
) -> tuple[bool, str | None, TopologyResolutionStatus, str | None]:
    """Determine whether a molecular formula uniquely defines a single-center star topology.

    Returns:
        (is_eligible, central_atom_symbol, status, reason_or_message)
    """

    atom_count = sum(parsed.atoms.values())
    if not (3 <= atom_count <= 7):
        return (
            False,
            None,
            TopologyResolutionStatus.UNSUPPORTED,
            f"Automatic inference supports 3 to 7 atoms in one covalent unit (formula has {atom_count}).",
        )

    # Homonuclear triatomics: e.g. O3, I3-
    if len(parsed.atoms) == 1 and atom_count == 3:
        elem = next(iter(parsed.atoms.keys()))
        return (True, elem, TopologyResolutionStatus.UNIQUE_FORMULA_TOPOLOGY, None)

    # Oxoacids with H + O + another nonmetal (e.g. HNO2, HNO3, H2SO4, H3PO4, HClO):
    # In oxoacids, H is bonded to O (-OH), creating a multi-center network rather than
    # direct H-to-central-atom bonding.
    elements = set(parsed.atoms.keys())
    if "H" in elements and "O" in elements and len(elements - {"H", "O"}) >= 1:
        return (
            False,
            None,
            TopologyResolutionStatus.AMBIGUOUS,
            "The molecular formula alone does not uniquely determine the connectivity for this oxoacid species. "
            "Please enter a chemical name or select a resolved structure.",
        )

    from app.chemistry.central_atom_rules import choose_central_atom
    from app.chemistry.periodic_table import get_element

    # If the least electronegative non-hydrogen element occurs more than once (e.g. N in N2O, O in H2O2),
    # the candidate central atom is repeated and connectivity cannot be uniquely determined as a single-center star.
    non_h = [e for e in parsed.atoms if e != "H"]
    if non_h:
        least_en = min(
            non_h,
            key=lambda e: (
                get_element(e).electronegativity if get_element(e).electronegativity is not None else 99.0,
                get_element(e).atomic_number,
            ),
        )
        if parsed.atoms[least_en] > 1:
            return (
                False,
                None,
                TopologyResolutionStatus.AMBIGUOUS,
                f"The least electronegative element '{least_en}' occurs multiple times in the formula. "
                "Connectivity cannot be uniquely assigned a single-center star topology from formula alone. "
                "Please enter a chemical name or select a resolved structure.",
            )

    try:
        central = choose_central_atom(parsed.atoms)
    except Exception as exc:
        return (
            False,
            None,
            TopologyResolutionStatus.AMBIGUOUS,
            f"Could not uniquely determine the central atom from the formula alone: {exc}",
        )

    # The chosen central atom must be present exactly once in a single-center topology.
    if parsed.atoms.get(central, 0) != 1:
        return (
            False,
            None,
            TopologyResolutionStatus.AMBIGUOUS,
            f"The potential central element '{central}' occurs multiple times in the formula. "
            "Connectivity cannot be uniquely assigned a single-center topology from formula alone. "
            "Please enter a chemical name or select a resolved structure.",
        )

    return (True, central, TopologyResolutionStatus.UNIQUE_FORMULA_TOPOLOGY, None)


def resolve_connectivity(
    *,
    smiles: str | None = None,
    molfile: str | None = None,
    pubchem_cid: int | None = None,
) -> ConnectivityResult:
    """Obtain a molecular graph from the best parser available.

    RDKit is preferred when enabled because it parses the full SMILES grammar; a
    PubChem molfile/SDF block (retrieved directly or via pubchem_cid) is the validated fallback.
    When neither is available the deterministic layer evaluates formula-topology uniqueness.
    """

    if molfile:
        graph = parse_molfile(molfile)
        if graph is not None:
            return ConnectivityResult(graph, _status("PubChem", ExternalServiceState.SUCCESS))

    if pubchem_cid is not None:
        from app.services.pubchem_service import fetch_pubchem_2d
        lookup = fetch_pubchem_2d(pubchem_cid)
        if lookup.data:
            graph = parse_molfile(lookup.data)
            if graph is not None:
                return ConnectivityResult(graph, _status("PubChem", ExternalServiceState.SUCCESS))

    if smiles and settings.ENABLE_RDKIT:
        graph = parse_smiles(smiles)
        if graph is not None:
            return ConnectivityResult(graph, _status("RDKit", ExternalServiceState.SUCCESS))
        return ConnectivityResult(None, _status(
            "RDKit", ExternalServiceState.INVALID_RESPONSE,
            "RDKit could not parse the supplied SMILES.",
        ))
    if smiles:
        return ConnectivityResult(None, _status(
            "RDKit", ExternalServiceState.DISABLED,
            "SMILES connectivity needs a real parser; RDKit is disabled.",
        ))
    return ConnectivityResult(None, _status(
        "PubChem", ExternalServiceState.CONFORMER_UNAVAILABLE,
        "No validated connectivity representation was available.",
    ))
