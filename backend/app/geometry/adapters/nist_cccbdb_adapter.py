"""The only place that knows what NIST CCCBDB HTML looks like.

Everything downstream consumes :class:`MolecularGeometryEvidence`, so CCCBDB's
page layout is confined to this adapter. Parsing is done with the standard
library ``html.parser`` -- CCCBDB publishes plain tables, and a scraping
dependency is not worth carrying for that.

What a real ``expgeom2x.asp`` page holds, and how each part is read:

* ``<H2>Point Group D<sub>3h</sub></H2>`` -- the point group, with its subscript.
* an "Internal coordinates" table with one row per *symmetry-unique* value: SO3 has a
  single ``rSO 1.418 (atoms 1 2)`` row for all three S–O bonds. Atoms are referenced
  by number; rows that reference a dummy atom (numbered past the real atoms, e.g. the
  ``X`` on a symmetry axis) are dropped.
* a Cartesian table whose rows CCCBDB never closes (``<TR><TD>P1 <TD>0.0000 ...``)
  and an atom-atom distance matrix. Their labels (P1, F2, ...) number the atoms.
* a reference table mapping each literature squib to its citation.

Each symmetry-unique value is expanded onto every bond or angle it describes, by
measuring CCCBDB's Cartesian coordinates. Those coordinates are not always faithful:
some pages carry another structure's (phosgene) or round them coarsely (ClO2,
ClF3), so they are trusted for measurement only when they reproduce every listed
value, and otherwise only to tell which atoms are equivalent. With no usable
coordinates a value is expanded only when it is the sole value of its kind around
the centre of a star-shaped molecule. A page that leaves any atom without a bond
length is refused. Published coordinates are passed on either way, as the fitter's
starting shape.

This is a best-effort reader of a third-party page, and the result is still checked
by :func:`app.geometry.fitter.fit_cartesian_coordinates`. Reviewed geometry belongs
in the local snapshot (``app/data/experimental_geometries.json``).
"""

from __future__ import annotations

import logging
import re
import socket
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from html.parser import HTMLParser
from itertools import combinations
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from app.core.config import settings
from app.geometry.fitter import (
    DEFAULT_ANGLE_TOLERANCE_DEG,
    DEFAULT_DIHEDRAL_TOLERANCE_DEG,
    DEFAULT_LENGTH_TOLERANCE_ANGSTROM,
    angle_degrees,
    dihedral_degrees,
    distance,
)
from app.schemas.geometry_evidence_schema import (
    BondAngleObservation,
    BondLengthObservation,
    DihedralObservation,
    GeometryAtom,
    GeometryBond,
    GeometryCoordinate,
    GeometryEvidenceType,
    GeometryIdentity,
    GeometryObservationSource,
    GeometrySource,
    MolecularGeometryEvidence,
)
from app.schemas.molecule_schema import ExternalServiceState

logger = logging.getLogger(__name__)

NIST_SERVICE_NAME = "NIST CCCBDB"

_ATOM_LABEL = re.compile(r"^([A-Z][a-z]?)(\d+)$")
_DESCRIPTOR = re.compile(r"^([rad])[A-Z][A-Za-z]*$")
_POINT_GROUP = re.compile(r"^point\s+group\s*(\S.*)$", re.IGNORECASE)
_KIND_BY_PREFIX = {"r": "bond_length", "a": "bond_angle", "d": "dihedral"}
_ATOMS_PER_KIND = {"bond_length": 2, "bond_angle": 3, "dihedral": 4}
_TOLERANCE = {
    "bond_length": DEFAULT_LENGTH_TOLERANCE_ANGSTROM,
    "bond_angle": DEFAULT_ANGLE_TOLERANCE_DEG,
    "dihedral": DEFAULT_DIHEDRAL_TOLERANCE_DEG,
}
_DERIVED_ANGLE_COMMENT = "Measured from the CCCBDB Cartesian coordinates; the page lists no separate value for it."

Vector = tuple[float, float, float]


# --------------------------------------------------------------------------- #
# HTML -> tables
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class _Table:
    heading: str
    rows: tuple[tuple[str, ...], ...]


@dataclass
class _OpenTable:
    heading: str
    rows: list[list[str]] = field(default_factory=list)
    row: list[str] | None = None
    cell: list[str] | None = None

    def close_cell(self) -> None:
        if self.cell is not None and self.row is not None:
            self.row.append(" ".join("".join(self.cell).split()))
        self.cell = None

    def close_row(self) -> None:
        self.close_cell()
        if self.row is not None:
            self.rows.append(self.row)
        self.row = None


class _TableCollector(HTMLParser):
    """Every table as rows of cell text, tagged with the nearest preceding heading.

    A new row or cell implicitly closes the open one, as a browser would: CCCBDB's
    coordinate table never closes its ``<TR>``/``<TD>`` tags. Heading text is joined
    without separators so ``D<sub>3h</sub>`` reads ``D3h``.
    """

    _HEADINGS = frozenset({"h1", "h2", "h3", "h4"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[_Table] = []
        self.headings: list[str] = []
        self._open: list[_OpenTable] = []
        self._heading_parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        current = self._open[-1] if self._open else None
        if tag == "table":
            self._open.append(_OpenTable(heading=self.headings[-1] if self.headings else ""))
        elif tag == "tr" and current is not None:
            current.close_row()
            current.row = []
        elif tag in {"td", "th"} and current is not None:
            current.close_cell()
            if current.row is None:
                current.row = []
            current.cell = []
        elif tag in self._HEADINGS:
            self._heading_parts = []

    def handle_endtag(self, tag: str) -> None:
        current = self._open[-1] if self._open else None
        if tag == "table" and current is not None:
            self._finish_table()
        elif tag == "tr" and current is not None:
            current.close_row()
        elif tag in {"td", "th"} and current is not None:
            current.close_cell()
        elif tag in self._HEADINGS and self._heading_parts is not None:
            text = " ".join("".join(self._heading_parts).split())
            if text:
                self.headings.append(text)
            self._heading_parts = None

    def handle_data(self, data: str) -> None:
        if self._open and self._open[-1].cell is not None:
            self._open[-1].cell.append(data)
        if self._heading_parts is not None:
            self._heading_parts.append(data)

    def close(self) -> None:
        super().close()
        while self._open:
            self._finish_table()

    def _finish_table(self) -> None:
        table = self._open.pop()
        table.close_row()
        self.tables.append(_Table(table.heading, tuple(tuple(row) for row in table.rows)))


# --------------------------------------------------------------------------- #
# Tables -> page content
# --------------------------------------------------------------------------- #


@dataclass(frozen=True, slots=True)
class _Row:
    """One internal-coordinate row; ``atoms`` are 0-based indices into the page's atoms."""

    kind: str
    atoms: tuple[int, ...]
    value: float
    squib: str | None
    comment: str | None


@dataclass(frozen=True, slots=True)
class _Page:
    elements: tuple[str, ...]
    rows: tuple[_Row, ...]
    coordinates: tuple[Vector, ...] | None
    point_group: str | None
    citations: dict[str, str]


def _collect(html: str) -> _TableCollector | None:
    collector = _TableCollector()
    try:
        collector.feed(html)
        collector.close()
    except (AssertionError, ValueError):
        logger.info("CCCBDB page could not be parsed as HTML")
        return None
    return collector


def _header(table: _Table) -> tuple[str, ...]:
    return tuple(cell.casefold() for cell in table.rows[0]) if table.rows else ()


def _is_label(cell: str) -> bool:
    return bool(_ATOM_LABEL.match(cell))


def _cartesian(tables: list[_Table]) -> list[tuple[str, Vector]] | None:
    """``[("P1", (x, y, z)), ...]`` from the table headed Atom | x | y | z."""

    for table in tables:
        header = _header(table)
        if len(header) < 4 or header[0] != "atom" or not all(header[i].startswith(axis) for i, axis in ((1, "x"), (2, "y"), (3, "z"))):
            continue
        atoms: list[tuple[str, Vector]] = []
        for row in table.rows[1:]:
            if len(row) < 4 or not _is_label(row[0]):
                continue
            try:
                atoms.append((row[0], (float(row[1]), float(row[2]), float(row[3]))))
            except ValueError:
                continue
        return atoms
    return None


def _distance_matrix_labels(tables: list[_Table]) -> list[str]:
    """Atom labels from the header row of the atom-atom distance matrix."""

    for table in tables:
        if not table.rows:
            continue
        first = table.rows[0]
        if len(first) >= 3 and not first[0].strip() and all(_is_label(cell) for cell in first[1:]):
            return list(first[1:])
    return []


def _internal_rows(tables: list[_Table], atom_count: int) -> list[_Row]:
    rows: list[_Row] = []
    for table in tables:
        if not table.heading.casefold().startswith("internal coordinates"):
            continue
        for cells in table.rows:
            match = _DESCRIPTOR.match(cells[0]) if cells else None
            if match is None or len(cells) < 6:
                continue
            kind = _KIND_BY_PREFIX[match.group(1)]
            try:
                value = float(cells[1])
            except ValueError:
                continue
            numbers = [int(cell) for cell in cells[2:6] if cell.isdigit()]
            if len(numbers) != _ATOMS_PER_KIND[kind] or not all(1 <= number <= atom_count for number in numbers):
                # A wrong arity, or a dummy atom (CCCBDB numbers those past the real atoms).
                continue
            rows.append(_Row(
                kind=kind, atoms=tuple(number - 1 for number in numbers), value=value,
                squib=(cells[6] if len(cells) > 6 and cells[6] else None),
                comment=(cells[7] if len(cells) > 7 and cells[7] else None),
            ))
    return rows


def _citations(tables: list[_Table]) -> dict[str, str]:
    for table in tables:
        if _header(table)[:2] == ("squib", "reference"):
            return {row[0]: row[1] for row in table.rows[1:] if len(row) >= 2 and row[0]}
    return {}


def _point_group(headings: list[str]) -> str | None:
    """``"C∞v"`` -> ``"Cinfv"``, the spelling the reviewed snapshot uses."""

    for heading in headings:
        match = _POINT_GROUP.match(heading)
        if match:
            return match.group(1).replace(" ", "").replace("∞", "inf") or None
    return None


def _read_page(html: str) -> _Page | None:
    collector = _collect(html)
    if collector is None:
        return None
    tables = collector.tables
    cartesian = _cartesian(tables)
    labels = [label for label, _ in cartesian] if cartesian else _distance_matrix_labels(tables)
    # CCCBDB numbers atoms by their label suffix; anything else cannot be trusted to
    # line up with the numbered references in the internal-coordinate table.
    if not labels or any(int(_ATOM_LABEL.match(label).group(2)) != index for index, label in enumerate(labels, 1)):
        return None
    coordinates = tuple(point for _, point in cartesian) if cartesian and len(cartesian) == len(labels) else None
    return _Page(
        elements=tuple(_ATOM_LABEL.match(label).group(1) for label in labels),
        rows=tuple(_internal_rows(tables, len(labels))),
        coordinates=coordinates,
        point_group=_point_group(collector.headings),
        citations=_citations(tables),
    )


def cccbdb_page_lists_no_geometry(html: str) -> bool:
    """True when the page is CCCBDB's answer for a species it has no geometry for.

    Such pages still render the section headings but carry no internal-coordinate
    table ("No coordinate data available.").
    """

    collector = _collect(html)
    if collector is None:
        return False
    has_title = any(heading.casefold().startswith("listing of experimental geometry data") for heading in collector.headings)
    has_internal = any(heading.casefold().startswith("internal coordinates") for heading in collector.headings)
    return has_title and not has_internal


# --------------------------------------------------------------------------- #
# Symmetry-unique rows -> every bond and angle they describe
# --------------------------------------------------------------------------- #


def _measure(kind: str, atoms: tuple[int, ...], points: tuple[Vector, ...]) -> float:
    if kind == "bond_length":
        return distance(points[atoms[0]], points[atoms[1]])
    if kind == "bond_angle":
        return angle_degrees(points[atoms[0]], points[atoms[1]], points[atoms[2]])
    return dihedral_degrees(*(points[index] for index in atoms))


def _agrees(kind: str, measured: float, value: float) -> bool:
    difference = measured - value
    if kind != "bond_length":
        difference = (difference + 180.0) % 360.0 - 180.0
    return abs(difference) <= _TOLERANCE[kind]


def _reproducing_coordinates(page: _Page) -> tuple[Vector, ...] | None:
    """CCCBDB's coordinates, or their mirror image, when they reproduce every row."""

    if page.coordinates is None:
        return None
    mirrored = tuple((-x, y, z) for x, y, z in page.coordinates)
    for points in (page.coordinates, mirrored):
        try:
            if all(_agrees(row.kind, _measure(row.kind, row.atoms, points), row.value) for row in page.rows):
                return points
        except ValueError:
            continue
    logger.info("CCCBDB Cartesian coordinates do not reproduce the page's internal coordinates; using them as hints only")
    return None


def _center(rows: tuple[_Row, ...], elements: tuple[str, ...]) -> int | None:
    """The atom at the vertex of the most angle rows, else the one every bond row shares."""

    vertices = Counter(row.atoms[1] for row in rows if row.kind == "bond_angle")
    if vertices:
        ranked = vertices.most_common()
        if len(ranked) == 1 or ranked[0][1] > ranked[1][1]:
            return ranked[0][0]
    bond_rows = [set(row.atoms) for row in rows if row.kind == "bond_length"]
    if not bond_rows:
        return None
    shared = sorted(set.intersection(*bond_rows))
    counts = Counter(elements)
    unique = [atom for atom in shared if counts[elements[atom]] == 1]
    return (unique or shared or [None])[0]


@dataclass
class _Expansion:
    bonds: list[tuple[_Row, list[tuple[int, ...]]]] = field(default_factory=list)
    angles: list[tuple[_Row | None, list[tuple[int, ...]], float]] = field(default_factory=list)


def _signature(elements: tuple[str, ...], atoms: tuple[int, ...]) -> tuple[str, ...]:
    """Element pattern of a bond (sorted ends) or an angle (sorted ends around the vertex)."""

    ends = sorted((elements[atoms[0]], elements[atoms[-1]]))
    return (ends[0], ends[1]) if len(atoms) == 2 else (ends[0], elements[atoms[1]], ends[1])


def _angle_key(triple: tuple[int, ...]) -> tuple[int, int, int]:
    return (min(triple[0], triple[2]), triple[1], max(triple[0], triple[2]))


class _Assigner:
    """Decides which further bonds/angles a symmetry-unique row describes.

    ``points`` are coordinates that reproduce every row: a candidate belongs to a row
    when it measures the row's value. ``hints`` are coordinates that do not reproduce
    the rows exactly but still show which atoms are equivalent (ClF3's are 0.05° off):
    a candidate belongs to the same-pattern row nearest its measured value, within a
    loose tolerance. Failing both, a row covers every same-pattern bond or angle around
    the centre of a star-shaped molecule, but only when no other row shares its pattern.
    """

    _HINT_TOLERANCE = {"bond_length": 0.05, "bond_angle": 2.0}

    def __init__(self, page: _Page, points: tuple[Vector, ...] | None, center: int | None) -> None:
        self.elements = page.elements
        self.rows = page.rows
        self.points = points
        self.hints = page.coordinates if points is None else None
        self.center = center
        self.star = center is not None and all(center in row.atoms for row in page.rows if row.kind == "bond_length")

    def _peers(self, row: _Row) -> list[_Row]:
        pattern = _signature(self.elements, row.atoms)
        return [other for other in self.rows if other.kind == row.kind and _signature(self.elements, other.atoms) == pattern]

    def _by_coordinates(self, row: _Row, candidate: tuple[int, ...]) -> bool:
        if self.points is not None:
            return _agrees(row.kind, _measure(row.kind, candidate, self.points), row.value)
        if self.hints is None:
            return False
        measured = _measure(row.kind, candidate, self.hints)
        nearest = min(self._peers(row), key=lambda other: abs(measured - other.value))
        return nearest is row and abs(measured - row.value) <= self._HINT_TOLERANCE[row.kind]

    def extend(self, row: _Row, candidates: list[tuple[int, ...]]) -> list[tuple[int, ...]]:
        matched = [candidate for candidate in candidates if self._by_coordinates(row, candidate)]
        if matched or self.points is not None:
            return matched
        if not self.star or len(self._peers(row)) != 1:
            return []
        if row.kind == "bond_length":
            return [candidate for candidate in candidates if self.center in row.atoms and self.center in candidate]
        return [candidate for candidate in candidates if row.atoms[1] == self.center and candidate[1] == self.center]


def _expand(page: _Page, points: tuple[Vector, ...] | None, center: int | None) -> _Expansion:
    elements = page.elements
    count = len(elements)
    assigner = _Assigner(page, points, center)
    expansion = _Expansion()

    claimed_bonds: set[frozenset[int]] = set()
    for row in (row for row in page.rows if row.kind == "bond_length"):
        listed = row.atoms
        candidates = [
            pair for pair in combinations(range(count), 2)
            if frozenset(pair) != frozenset(listed) and frozenset(pair) not in claimed_bonds
            and _signature(elements, pair) == _signature(elements, listed)
        ]
        pairs = [listed, *assigner.extend(row, candidates)]
        claimed_bonds.update(frozenset(pair) for pair in pairs)
        expansion.bonds.append((row, pairs))

    neighbors: dict[int, set[int]] = {atom: set() for atom in range(count)}
    for pair in claimed_bonds:
        first, second = sorted(pair)
        neighbors[first].add(second)
        neighbors[second].add(first)

    claimed_angles: set[tuple[int, int, int]] = set()
    for row in (row for row in page.rows if row.kind == "bond_angle"):
        listed = row.atoms
        candidates = [
            (first, middle, second)
            for middle in range(count)
            for first, second in combinations(sorted(neighbors[middle]), 2)
            if _signature(elements, (first, middle, second)) == _signature(elements, listed)
            and _angle_key((first, middle, second)) not in {_angle_key(listed), *claimed_angles}
        ]
        triples = [listed, *assigner.extend(row, candidates)]
        claimed_angles.update(_angle_key(triple) for triple in triples)
        expansion.angles.append((row, triples, row.value))

    if points is not None:
        # Symmetry fixes some angles that CCCBDB therefore never lists (BCl3, PF5);
        # coordinates that reproduce every listed value still carry them.
        derived: dict[tuple[tuple[str, ...], float], list[tuple[int, ...]]] = {}
        for middle in range(count):
            for first, second in combinations(sorted(neighbors[middle]), 2):
                triple = (first, middle, second)
                if _angle_key(triple) in claimed_angles:
                    continue
                value = round(angle_degrees(points[first], points[middle], points[second]), 2)
                derived.setdefault((_signature(elements, triple), value), []).append(triple)
        for (_, value), triples in derived.items():
            expansion.angles.append((None, triples, value))
    return expansion


# --------------------------------------------------------------------------- #
# Page -> evidence
# --------------------------------------------------------------------------- #


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

    Returns ``None`` when the page has no internal coordinates, when its atoms do not
    match ``identity.atom_inventory`` (a page for another species), or when the rows
    cannot be tied to numbered atoms.
    """

    page = _read_page(html)
    if page is None or not page.rows:
        logger.info("CCCBDB page contained no usable internal coordinates")
        return None
    if identity.atom_inventory and dict(Counter(page.elements)) != identity.atom_inventory:
        logger.info("CCCBDB atoms %s do not match requested inventory %s", dict(Counter(page.elements)), identity.atom_inventory)
        return None

    points = _reproducing_coordinates(page)
    center = _center(page.rows, page.elements)
    expansion = _expand(page, points, center)
    bonded = {atom for _, pairs in expansion.bonds for pair in pairs for atom in pair}
    if len(bonded) != len(page.elements):
        # An atom with no bond length is free to sit anywhere: not a usable geometry.
        logger.info("CCCBDB rows leave %d of %d atoms without a bond length", len(page.elements) - len(bonded), len(page.elements))
        return None
    if center is None:
        degree = Counter(atom for _, pairs in expansion.bonds for pair in pairs for atom in pair)
        center = degree.most_common(1)[0][0]

    order = [center, *(atom for atom in range(len(page.elements)) if atom != center)]
    ids = {atom: f"a{index}" for index, atom in enumerate(order)}
    elements = page.elements
    retrieved = retrieved_at or datetime.now(UTC)

    def source(row: _Row | None) -> GeometryObservationSource:
        return GeometryObservationSource(
            source_name=NIST_SERVICE_NAME, source_reference=row.squib if row else None, source_url=source_url,
            comment=(row.comment if row else _DERIVED_ANGLE_COMMENT), retrieval_timestamp=retrieved,
        )

    bond_lengths: list[BondLengthObservation] = []
    bonds: list[GeometryBond] = []
    for group, (row, pairs) in enumerate(expansion.bonds):
        for index, (first, second) in enumerate(pairs):
            if second == center:
                first, second = second, first
            bonds.append(GeometryBond(atom1_id=ids[first], atom2_id=ids[second], order=1))
            bond_lengths.append(BondLengthObservation(
                id=f"len-{group}-{index}", atom1_id=ids[first], atom2_id=ids[second], value_angstrom=row.value,
                equivalent_count=len(pairs), label=f"{elements[first]}–{elements[second]}", source=source(row),
            ))

    bond_angles = [
        BondAngleObservation(
            id=f"ang-{group}-{index}", atom1_id=ids[first], center_atom_id=ids[middle], atom2_id=ids[second],
            value_deg=value, equivalent_count=len(triples),
            label=f"{elements[first]}–{elements[middle]}–{elements[second]}", source=source(row),
        )
        for group, (row, triples, value) in enumerate(expansion.angles)
        for index, (first, middle, second) in enumerate(triples)
    ]
    dihedrals = [
        DihedralObservation(
            id=f"dih-{index}", atom1_id=ids[row.atoms[0]], atom2_id=ids[row.atoms[1]], atom3_id=ids[row.atoms[2]],
            atom4_id=ids[row.atoms[3]], value_deg=row.value, label="–".join(elements[atom] for atom in row.atoms),
            source=source(row),
        )
        for index, row in enumerate(row for row in page.rows if row.kind == "dihedral")
    ]

    published = points or page.coordinates
    squibs = list(dict.fromkeys(row.squib for row in page.rows if row.squib))
    cited = [page.citations[squib] for squib in squibs if squib in page.citations]
    try:
        return MolecularGeometryEvidence(
            id=record_id or f"nist-cccbdb-{identity.formula.casefold()}-{identity.cas_rn or identity.inchikey or 'unkeyed'}",
            identity=identity,
            evidence_type=GeometryEvidenceType.EXPERIMENTAL,
            atoms=[
                GeometryAtom(id=ids[atom], element=elements[atom], role="center" if atom == center else "ligand")
                for atom in order
            ],
            bonds=bonds,
            bond_lengths=bond_lengths,
            bond_angles=bond_angles,
            dihedrals=dihedrals,
            # Coordinates that miss the listed values are still the best starting shape
            # the fitter can get; it refits them and validates the result either way.
            coordinates=[
                GeometryCoordinate(id=ids[atom], element=elements[atom], x=published[atom][0], y=published[atom][1], z=published[atom][2])
                for atom in order
            ] if published is not None else None,
            phase="gas",
            point_group=page.point_group,
            source=GeometrySource(
                name=NIST_SERVICE_NAME,
                reference=reference or ("; ".join(squibs) or None),
                url=source_url,
                comments=comments or (
                    f"{'; '.join(cited)}, as tabulated by NIST CCCBDB." if cited
                    else "Experimental gas-phase geometry retrieved from the NIST CCCBDB experimental geometry page."
                ),
                retrieved_at=retrieved,
            ),
        )
    except ValidationError as error:
        logger.info("CCCBDB page produced an inconsistent geometry record: %s", error)
        return None




def cccbdb_url(cas_rn: str, charge: int = 0) -> str:
    """CCCBDB keys its experimental-geometry pages on the digits of a CAS number and charge."""

    clean_cas = re.sub(r"[^0-9]", "", cas_rn)
    return f"{settings.NIST_CCCBDB_BASE_URL.rstrip('/')}/expgeom2x.asp?casno={clean_cas}&charge={charge}"


def fetch_cccbdb_geometry_html(
    cas_rn: str,
    *,
    charge: int = 0,
    timeout: float | None = None,
) -> tuple[str | None, ExternalServiceState]:
    """Fetch one CCCBDB page under a bounded timeout; never raises."""

    url = cccbdb_url(cas_rn, charge)
    effective_timeout = settings.NIST_TIMEOUT_SECONDS if timeout is None else min(settings.NIST_TIMEOUT_SECONDS, timeout)
    if effective_timeout <= 0:
        return None, ExternalServiceState.TIMEOUT
    try:
        request = Request(url, headers={"User-Agent": "VSEPR-AI/1.0 educational-app"})
        with urlopen(request, timeout=effective_timeout) as response:
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
