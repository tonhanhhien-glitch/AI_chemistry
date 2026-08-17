"""The only place that knows what NIST CCCBDB HTML looks like.

Everything downstream consumes :class:`MolecularGeometryEvidence`, so CCCBDB's
page layout is confined to this adapter. Parsing is done with the standard
library ``html.parser`` -- CCCBDB publishes plain tables, and a scraping
dependency is not worth carrying for that.

The adapter normalises CCCBDB's ``Element+index`` atom labels (``Cl1``, ``F2``)
into stable atom ids, derives the central atom from the angle rows rather than
from any per-molecule knowledge, and returns ``None`` whenever the page does not
contain a complete, self-consistent geometry.
"""

from __future__ import annotations

import logging
import re
import socket
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings
from app.schemas.geometry_evidence_schema import (
    BondAngleObservation,
    BondLengthObservation,
    DihedralObservation,
    GeometryAtom,
    GeometryBond,
    GeometryEvidenceType,
    GeometryIdentity,
    GeometrySource,
    MolecularGeometryEvidence,
)
from app.schemas.molecule_schema import ExternalServiceState

logger = logging.getLogger(__name__)

NIST_SERVICE_NAME = "NIST CCCBDB"

_ATOM_LABEL = re.compile(r"^([A-Z][a-z]?)(\d*)$")
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
_POINT_GROUP = re.compile(r"point\s+group[^A-Za-z0-9]*([A-Za-z][\w*]*)", re.IGNORECASE)
_STATE = re.compile(r"electronic\s+state[^A-Za-z0-9]*([^\n<]{1,32})", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class _Table:
    heading: str
    rows: tuple[tuple[str, ...], ...]


class _TableCollector(HTMLParser):
    """Collect every table as a matrix of cell strings, tagged with nearby heading text."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[_Table] = []
        self.text_parts: list[str] = []
        self._table_stack: list[list[list[str]]] = []
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._heading: str = ""
        self._pending_heading: list[str] = []
        self._in_heading = False
        self._table_headings: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._table_stack.append([])
            self._table_headings.append(self._heading)
        elif tag == "tr" and self._table_stack:
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []
        elif tag in {"h1", "h2", "h3", "h4", "caption", "p"}:
            self._in_heading = True
            self._pending_heading = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "table" and self._table_stack:
            rows = self._table_stack.pop()
            heading = self._table_headings.pop() if self._table_headings else ""
            flat = " ".join(cell for row in rows[:1] for cell in row)
            self.tables.append(_Table(f"{heading} {flat}".strip(), tuple(tuple(row) for row in rows)))
        elif tag == "tr" and self._row is not None:
            if self._table_stack:
                self._table_stack[-1].append(self._row)
            self._row = None
        elif tag in {"td", "th"} and self._cell is not None and self._row is not None:
            self._row.append(" ".join("".join(self._cell).split()))
            self._cell = None
        elif tag in {"h1", "h2", "h3", "h4", "caption", "p"} and self._in_heading:
            text = " ".join("".join(self._pending_heading).split())
            if text:
                self._heading = text
            self._in_heading = False

    def handle_data(self, data: str) -> None:
        self.text_parts.append(data)
        if self._cell is not None:
            self._cell.append(data)
        if self._in_heading:
            self._pending_heading.append(data)


def _split_label_chain(value: str) -> list[str] | None:
    """``"F2-Cl1-F3"`` -> ``["F2", "Cl1", "F3"]``; ``None`` when it is not an atom chain."""

    parts = [part.strip() for part in re.split(r"[-–—]", value) if part.strip()]
    if len(parts) < 2:
        return None
    return parts if all(_ATOM_LABEL.match(part) for part in parts) else None


def _atom_chain(cells: tuple[str, ...], expected: int) -> list[str] | None:
    """Accept both ``"F2-Cl1-F3"`` in one cell and ``"F2" "Cl1" "F3"`` in separate cells."""

    for cell in cells:
        chain = _split_label_chain(cell)
        if chain is not None and len(chain) == expected:
            return chain
    labels = [cell for cell in cells if _ATOM_LABEL.match(cell)]
    return labels[:expected] if len(labels) >= expected else None


def _row_value(cells: tuple[str, ...]) -> float | None:
    for cell in reversed(cells):
        if _ATOM_LABEL.match(cell) or _split_label_chain(cell):
            continue
        match = _NUMBER.search(cell)
        if match:
            return float(match.group())
    return None


def _classify(heading: str) -> str | None:
    lowered = heading.casefold()
    if "dihedral" in lowered or "torsion" in lowered:
        return "dihedral"
    if "angle" in lowered:
        return "bond_angle"
    if "length" in lowered or "distance" in lowered or "bond" in lowered:
        return "bond_length"
    return None


def parse_cccbdb_geometry_html(
    html: str,
    *,
    identity: GeometryIdentity,
    source_url: str,
    reference: str | None = None,
    comments: str | None = None,
    retrieved_at: datetime | None = None,
    record_id: str | None = None,
) -> MolecularGeometryEvidence | None:
    """Normalise a CCCBDB experimental-geometry page into geometry evidence.

    Returns ``None`` when the page holds no usable geometry, when the atom labels
    disagree with the requested atom inventory, or when the observations do not
    describe a single connected centre. A malformed page must never become a
    half-populated record.
    """

    collector = _TableCollector()
    try:
        collector.feed(html)
        collector.close()
    except (AssertionError, ValueError):
        logger.info("CCCBDB page could not be parsed as HTML")
        return None

    lengths: list[tuple[list[str], float]] = []
    angles: list[tuple[list[str], float]] = []
    dihedrals: list[tuple[list[str], float]] = []
    for table in collector.tables:
        kind = _classify(table.heading)
        if kind is None:
            continue
        expected = {"bond_length": 2, "bond_angle": 3, "dihedral": 4}[kind]
        for row in table.rows:
            chain = _atom_chain(row, expected)
            value = _row_value(row)
            if chain is None or value is None:
                continue
            if len(set(chain)) != expected:
                continue
            {"bond_length": lengths, "bond_angle": angles, "dihedral": dihedrals}[kind].append((chain, value))

    if not lengths and not angles:
        logger.info("CCCBDB page contained no bond-length or bond-angle rows")
        return None

    labels: list[str] = []
    for chain, _value in [*lengths, *angles, *dihedrals]:
        for label in chain:
            if label not in labels:
                labels.append(label)

    elements: dict[str, str] = {}
    for label in labels:
        match = _ATOM_LABEL.match(label)
        if match is None:
            return None
        elements[label] = match.group(1)

    inventory: dict[str, int] = {}
    for element in elements.values():
        inventory[element] = inventory.get(element, 0) + 1
    if identity.atom_inventory and inventory != identity.atom_inventory:
        logger.info("CCCBDB atom labels %s do not match the requested inventory %s", inventory, identity.atom_inventory)
        return None

    centre_counts: dict[str, int] = {}
    for chain, _value in angles:
        centre_counts[chain[1]] = centre_counts.get(chain[1], 0) + 1
    centre = max(centre_counts, key=lambda key: centre_counts[key]) if centre_counts else None
    if centre is None and lengths:
        shared = set(lengths[0][0])
        for chain, _value in lengths[1:]:
            shared &= set(chain)
        centre = next(iter(sorted(shared)), None)
    if centre is None:
        return None

    ordered = [centre, *[label for label in labels if label != centre]]
    identifier = {label: f"a{index}" for index, label in enumerate(ordered)}

    text = " ".join(collector.text_parts)
    point_group = _POINT_GROUP.search(text)
    electronic_state = _STATE.search(text)

    bonds = [
        GeometryBond(atom1_id=identifier[centre], atom2_id=identifier[label], order=1)
        for label in ordered[1:]
    ]
    evidence = MolecularGeometryEvidence(
        id=record_id or f"nist-cccbdb-{identity.formula.casefold()}-{identity.cas_rn or identity.inchikey or 'unkeyed'}",
        identity=identity,
        evidence_type=GeometryEvidenceType.EXPERIMENTAL,
        atoms=[
            GeometryAtom(id=identifier[label], element=elements[label], role="center" if label == centre else "ligand")
            for label in ordered
        ],
        bonds=bonds,
        bond_lengths=[
            BondLengthObservation(
                id=f"len-{index}", atom1_id=identifier[chain[0]], atom2_id=identifier[chain[1]],
                value_angstrom=value, label=f"{elements[chain[0]]}–{elements[chain[1]]}",
            )
            for index, (chain, value) in enumerate(lengths)
        ],
        bond_angles=[
            BondAngleObservation(
                id=f"ang-{index}", atom1_id=identifier[chain[0]], center_atom_id=identifier[chain[1]],
                atom2_id=identifier[chain[2]], value_deg=value,
                label=f"{elements[chain[0]]}–{elements[chain[1]]}–{elements[chain[2]]}",
            )
            for index, (chain, value) in enumerate(angles)
        ],
        dihedrals=[
            DihedralObservation(
                id=f"dih-{index}", atom1_id=identifier[chain[0]], atom2_id=identifier[chain[1]],
                atom3_id=identifier[chain[2]], atom4_id=identifier[chain[3]], value_deg=value,
                label="–".join(elements[label] for label in chain),
            )
            for index, (chain, value) in enumerate(dihedrals)
        ],
        coordinates=None,
        phase="gas",
        electronic_state=electronic_state.group(1).strip() if electronic_state else None,
        point_group=point_group.group(1) if point_group else None,
        source=GeometrySource(
            name=NIST_SERVICE_NAME,
            reference=reference,
            url=source_url,
            comments=comments or "Experimental gas-phase geometry retrieved from the NIST CCCBDB experimental geometry page.",
            retrieved_at=retrieved_at or datetime.now(UTC),
        ),
    )
    return evidence


def cccbdb_url(cas_rn: str) -> str:
    """CCCBDB keys its experimental-geometry pages on the digits of a CAS number."""

    return f"{settings.NIST_CCCBDB_BASE_URL.rstrip('/')}/exp2x.asp?casno={re.sub(r'[^0-9]', '', cas_rn)}"


def fetch_cccbdb_geometry_html(cas_rn: str) -> tuple[str | None, ExternalServiceState]:
    """Fetch one CCCBDB page under a bounded timeout; never raises."""

    url = cccbdb_url(cas_rn)
    try:
        request = Request(url, headers={"User-Agent": "VSEPR-AI/1.0 educational-app"})
        with urlopen(request, timeout=settings.NIST_TIMEOUT_SECONDS) as response:
            payload = response.read()
    except HTTPError as error:
        if error.code in {400, 404}:
            return None, ExternalServiceState.NOT_FOUND
        if error.code == 429:
            return None, ExternalServiceState.RATE_LIMITED
        if 500 <= error.code < 600:
            return None, ExternalServiceState.TEMPORARY_FAILURE
        return None, ExternalServiceState.INVALID_RESPONSE
    except (TimeoutError, socket.timeout):
        return None, ExternalServiceState.TIMEOUT
    except (URLError, OSError):
        return None, ExternalServiceState.TEMPORARY_FAILURE
    try:
        return payload.decode("utf-8", errors="replace"), ExternalServiceState.SUCCESS
    except (UnicodeDecodeError, AttributeError):
        return None, ExternalServiceState.INVALID_RESPONSE
