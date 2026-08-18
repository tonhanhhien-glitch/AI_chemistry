"""The only place that knows what NIST CCCBDB HTML looks like.

Everything downstream consumes :class:`MolecularGeometryEvidence`, so CCCBDB's
page layout is confined to this adapter. Parsing is done with the standard
library ``html.parser`` -- CCCBDB publishes plain tables, and a scraping
dependency is not worth carrying for that.

The adapter normalises CCCBDB's internal-coordinate and Cartesian coordinate
tables into stable atom ids, derives the central atom from the angle rows or star
topology, and returns ``None`` whenever the page does not contain a complete,
self-consistent geometry.
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

_ATOM_LABEL = re.compile(r"^([A-Z][a-z]?)(\d*)$")
_NUMBER = re.compile(r"-?\d+(?:\.\d+)?")
_POINT_GROUP = re.compile(r"point\s+group[^A-Za-z0-9]*([A-Za-z][\w*]*)", re.IGNORECASE)
_STATE = re.compile(r"electronic\s+state[^A-Za-z0-9]*([^\n<]{1,32})", re.IGNORECASE)
_ELEMENT_ONLY = re.compile(r"^[A-Z][a-z]?$")


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
    """``"F2-Cl1-F3"`` or ``"2 1 3"`` -> ``["F2", "Cl1", "F3"]`` or ``["2", "1", "3"]``."""

    parts = [part.strip() for part in re.split(r"[-–—/\s]+", value) if part.strip()]
    if len(parts) < 2:
        return None
    return parts if all(_ATOM_LABEL.match(part) or (part.isdigit() and 1 <= int(part) <= 50) for part in parts) else None


def _is_cartesian_table(table: _Table) -> bool:
    """Check if table represents Cartesian coordinates (e.g. X, Y, Z coordinates)."""
    lowered = table.heading.casefold()
    if "internal" in lowered:
        return False
    if "cartesian" in lowered or "xyz" in lowered:
        return True
    if len(table.rows) > 1:
        header = [c.casefold() for c in table.rows[0]]
        if sum(1 for h in ("x", "y", "z") if h in header) >= 2:
            return True
    return False


def _parse_cartesian_table(table: _Table) -> dict[str, tuple[str, float, float, float]] | None:
    """Extract {atom_label_or_id: (element, x, y, z)} from a Cartesian coordinates table."""
    results: dict[str, tuple[str, float, float, float]] = {}
    start_row = 1 if any(any(c.casefold() in ("x", "y", "z", "atom", "element") for c in row) for row in table.rows[:1]) else 0

    for idx, row in enumerate(table.rows[start_row:], start=1):
        if len(row) < 4:
            continue
        # Row might be: ['1', 'Cl', '0.0', '0.0', '0.0'] or ['Cl1', '0.0', '0.0', '0.0'] or ['Cl', '0.0', '0.0', '0.0']
        # Find 3 consecutive floating point numbers
        num_indices: list[int] = []
        for c_idx, cell in enumerate(row):
            try:
                float(cell)
                num_indices.append(c_idx)
            except ValueError:
                pass
        if len(num_indices) < 3:
            continue
        # take last 3 numbers as x, y, z
        x_idx, y_idx, z_idx = num_indices[-3:]
        x, y, z = float(row[x_idx]), float(row[y_idx]), float(row[z_idx])
        # Find element and label
        element: str | None = None
        label: str | None = None
        for c_idx in range(x_idx):
            cell = row[c_idx].strip()
            match = _ATOM_LABEL.match(cell)
            if match:
                elem, num = match.group(1), match.group(2)
                element = elem
                label = cell if num else f"{elem}{idx}"
                break
        if element is None:
            # check if first cell is index and second cell is element
            if len(row) > 1 and _ELEMENT_ONLY.match(row[1].strip()):
                element = row[1].strip()
                label = f"{element}{row[0].strip()}"
        if element and label:
            results[label] = (element, x, y, z)

    return results if results else None


def _classify_descriptor(desc: str) -> str | None:
    """Classify internal coordinate from descriptor prefix: r -> length, a -> angle, d/t -> dihedral."""
    clean = desc.strip()
    if not clean:
        return None
    char = clean[0].lower()
    if char == "r":
        return "bond_length"
    if char in ("a", "∠"):
        return "bond_angle"
    if char in ("d", "t"):
        return "dihedral"
    return None


def _classify_heading(heading: str) -> str | None:
    lowered = heading.casefold()
    if "dihedral" in lowered or "torsion" in lowered:
        return "dihedral"
    if "angle" in lowered:
        return "bond_angle"
    if "length" in lowered or "distance" in lowered or "bond" in lowered:
        return "bond_length"
    return None


@dataclass
class _RawObservation:
    kind: str
    atoms: list[str]
    value: float
    reference: str | None = None
    comment: str | None = None


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

    Handles real CCCBDB internal coordinates tables (with descriptors r..., a..., d...),
    numeric atom references (e.g. 2 1 3), atom-label chains (e.g. F2-Cl1-F3), Cartesian
    coordinate tables, and per-observation references and comments.
    """

    collector = _TableCollector()
    try:
        collector.feed(html)
        collector.close()
    except (AssertionError, ValueError):
        logger.info("CCCBDB page could not be parsed as HTML")
        return None

    cartesian_map: dict[str, tuple[str, float, float, float]] | None = None
    raw_observations: list[_RawObservation] = []

    for table in collector.tables:
        if _is_cartesian_table(table):
            coords = _parse_cartesian_table(table)
            if coords:
                cartesian_map = coords

    for table in collector.tables:
        if _is_cartesian_table(table):
            continue
        table_kind = _classify_heading(table.heading)

        for row in table.rows:
            if not row:
                continue
            # Look for descriptor in first column (e.g. rCl-F1, aF1-Cl-F2, d...)
            row_kind = _classify_descriptor(row[0]) or table_kind
            if row_kind is None:
                continue
            expected_atoms = {"bond_length": 2, "bond_angle": 3, "dihedral": 4}[row_kind]

            chain = None
            chain_cell_idx: int | None = None
            val: float | None = None
            ref: str | None = None
            comment_text: str | None = None

            for idx, cell in enumerate(row):
                parts = _split_label_chain(cell)
                if parts and len(parts) == expected_atoms:
                    chain = parts
                    chain_cell_idx = idx
                    break

            if chain is None:
                # Check for individual atom cells: e.g. row: [desc, val, atom1, atom2, atom3, ref, comm]
                # Or row: [atom1, atom2, atom3, val, ref]
                atom_cells: list[str] = []
                for cell in row:
                    stripped = cell.strip()
                    if _ATOM_LABEL.match(stripped) and not stripped.replace(".", "").isdigit():
                        atom_cells.append(stripped)
                    elif stripped.isdigit() and 1 <= int(stripped) <= 20:
                        # Numeric atom reference: e.g. "2", "1", "3"
                        atom_cells.append(stripped)
                if len(atom_cells) >= expected_atoms:
                    chain = atom_cells[:expected_atoms]

            # Extract numeric value
            for idx, cell in enumerate(row):
                if chain_cell_idx is not None and idx == chain_cell_idx:
                    continue
                cell_stripped = cell.strip()
                if chain and cell_stripped in chain:
                    continue
                match = _NUMBER.search(cell_stripped)
                if match:
                    try:
                        num = float(match.group())
                        # Length > 0, Angle [0, 180], Dihedral [-180, 180]
                        if row_kind == "bond_length" and 0.4 <= num <= 5.0:
                            val = num
                            break
                        elif row_kind in ("bond_angle", "dihedral") and 0.0 <= abs(num) <= 180.0:
                            val = num
                            break
                    except ValueError:
                        pass

            if chain is not None and val is not None and len(set(chain)) == expected_atoms:
                # Look for reference and comment in remaining cells
                for cell in row[expected_atoms:]:
                    c_clean = cell.strip()
                    if not c_clean or c_clean == str(val):
                        continue
                    if any(yr in c_clean for yr in ("19", "20")) or "[" in c_clean or len(c_clean) > 4:
                        if ref is None:
                            ref = c_clean
                        elif comment_text is None:
                            comment_text = c_clean

                raw_observations.append(_RawObservation(
                    kind=row_kind,
                    atoms=chain,
                    value=val,
                    reference=ref,
                    comment=comment_text,
                ))

    if not raw_observations:
        logger.info("CCCBDB page contained no valid geometric observations")
        return None

    # Resolve atom labels: if atoms are numeric e.g. "1", "2", "3", map to elements from identity or cartesian table
    # Collect all atom identifiers
    all_raw_atoms: list[str] = []
    for obs in raw_observations:
        for a in obs.atoms:
            if a not in all_raw_atoms:
                all_raw_atoms.append(a)

    atom_element_map: dict[str, str] = {}
    numeric_indices = all(a.isdigit() for a in all_raw_atoms)

    if numeric_indices:
        # 1-indexed atom table
        if cartesian_map:
            for idx_str in all_raw_atoms:
                idx = int(idx_str)
                # match with cartesian_map order
                cart_keys = list(cartesian_map.keys())
                if 1 <= idx <= len(cart_keys):
                    key = cart_keys[idx - 1]
                    atom_element_map[idx_str] = cartesian_map[key][0]
        elif identity.atom_inventory:
            # Infer from atom inventory: e.g. Cl:1, F:3 -> 1: Cl, 2: F, 3: F, 4: F
            flat_elements: list[str] = []
            # non-terminal first
            for elem, count in sorted(identity.atom_inventory.items(), key=lambda item: item[1]):
                flat_elements.extend([elem] * count)
            for a in all_raw_atoms:
                idx = int(a)
                if 1 <= idx <= len(flat_elements):
                    atom_element_map[a] = flat_elements[idx - 1]
    else:
        for a in all_raw_atoms:
            match = _ATOM_LABEL.match(a)
            if match:
                atom_element_map[a] = match.group(1)

    if len(atom_element_map) != len(all_raw_atoms):
        logger.info("Could not map all CCCBDB atom labels to elements")
        return None

    # Validate atom inventory if specified
    inventory: dict[str, int] = {}
    for element in atom_element_map.values():
        inventory[element] = inventory.get(element, 0) + 1
    if identity.atom_inventory and inventory != identity.atom_inventory:
        logger.info("CCCBDB atom labels %s do not match requested inventory %s", inventory, identity.atom_inventory)
        return None

    # Determine central atom: the atom that appears most frequently as center in angles, or shared in lengths
    centre_counts: dict[str, int] = {}
    for obs in raw_observations:
        if obs.kind == "bond_angle" and len(obs.atoms) == 3:
            centre_counts[obs.atoms[1]] = centre_counts.get(obs.atoms[1], 0) + 1
    centre = max(centre_counts, key=lambda k: centre_counts[k]) if centre_counts else None
    if centre is None:
        lengths = [obs for obs in raw_observations if obs.kind == "bond_length"]
        if lengths:
            shared = set(lengths[0].atoms)
            for l in lengths[1:]:
                shared &= set(l.atoms)
            centre = next(iter(sorted(shared)), None)
    if centre is None and all_raw_atoms:
        centre = all_raw_atoms[0]
    if centre is None:
        return None

    ordered = [centre, *[a for a in all_raw_atoms if a != centre]]
    identifier = {label: f"a{index}" for index, label in enumerate(ordered)}

    text = " ".join(collector.text_parts)
    point_group = _POINT_GROUP.search(text)
    electronic_state = _STATE.search(text)

    # Build observation lists
    bond_lengths: list[BondLengthObservation] = []
    bond_angles: list[BondAngleObservation] = []
    dihedrals: list[DihedralObservation] = []

    for idx, obs in enumerate(raw_observations):
        obs_source = None
        if obs.reference or obs.comment:
            obs_source = GeometryObservationSource(
                source_name=NIST_SERVICE_NAME,
                source_reference=obs.reference,
                source_url=source_url,
                comment=obs.comment,
                retrieval_timestamp=retrieved_at or datetime.now(UTC),
            )
        if obs.kind == "bond_length":
            a1, a2 = obs.atoms[0], obs.atoms[1]
            bond_lengths.append(BondLengthObservation(
                id=f"len-{idx}",
                atom1_id=identifier[a1],
                atom2_id=identifier[a2],
                value_angstrom=obs.value,
                label=f"{atom_element_map[a1]}–{atom_element_map[a2]}",
                source=obs_source,
            ))
        elif obs.kind == "bond_angle":
            a1, c, a2 = obs.atoms[0], obs.atoms[1], obs.atoms[2]
            bond_angles.append(BondAngleObservation(
                id=f"ang-{idx}",
                atom1_id=identifier[a1],
                center_atom_id=identifier[c],
                atom2_id=identifier[a2],
                value_deg=obs.value,
                label=f"{atom_element_map[a1]}–{atom_element_map[c]}–{atom_element_map[a2]}",
                source=obs_source,
            ))
        elif obs.kind == "dihedral":
            a1, a2, a3, a4 = obs.atoms[0], obs.atoms[1], obs.atoms[2], obs.atoms[3]
            dihedrals.append(DihedralObservation(
                id=f"dih-{idx}",
                atom1_id=identifier[a1],
                atom2_id=identifier[a2],
                atom3_id=identifier[a3],
                atom4_id=identifier[a4],
                value_deg=obs.value,
                label="–".join(atom_element_map[a] for a in (a1, a2, a3, a4)),
                source=obs_source,
            ))

    bonds = [
        GeometryBond(atom1_id=identifier[centre], atom2_id=identifier[label], order=1)
        for label in ordered[1:]
    ]

    # Check if authoritative Cartesian coordinates are available covering all ordered atoms
    parsed_coordinates: list[GeometryCoordinate] | None = None
    if cartesian_map and len(cartesian_map) == len(ordered):
        try:
            parsed_coordinates = []
            cart_keys = list(cartesian_map.keys())
            for label in ordered:
                coord_match: tuple[str, float, float, float] | None = None
                if label in cartesian_map:
                    coord_match = cartesian_map[label]
                elif label.isdigit():
                    idx = int(label)
                    for k, val in cartesian_map.items():
                        m = re.search(r"(\d+)$", k)
                        if m and int(m.group(1)) == idx:
                            coord_match = val
                            break
                    if coord_match is None and 1 <= idx <= len(cart_keys):
                        coord_match = cartesian_map[cart_keys[idx - 1]]
                else:
                    match = _ATOM_LABEL.match(label)
                    if match and match.group(2):
                        target_num = int(match.group(2))
                        for k, val in cartesian_map.items():
                            m = re.search(r"(\d+)$", k)
                            if m and int(m.group(1)) == target_num:
                                coord_match = val
                                break
                    if coord_match is None:
                        elem = atom_element_map.get(label)
                        if elem:
                            matching_keys = [k for k in cart_keys if cartesian_map[k][0] == elem]
                            same_elem_ordered = [a for a in ordered if atom_element_map.get(a) == elem]
                            if label in same_elem_ordered:
                                pos = same_elem_ordered.index(label)
                                if pos < len(matching_keys):
                                    coord_match = cartesian_map[matching_keys[pos]]

                if coord_match is not None:
                    elem, x, y, z = coord_match
                    parsed_coordinates.append(GeometryCoordinate(
                        id=identifier[label],
                        element=elem,
                        x=x, y=y, z=z,
                    ))
                else:
                    parsed_coordinates = None
                    break
        except Exception:
            parsed_coordinates = None

    evidence = MolecularGeometryEvidence(
        id=record_id or f"nist-cccbdb-{identity.formula.casefold()}-{identity.cas_rn or identity.inchikey or 'unkeyed'}",
        identity=identity,
        evidence_type=GeometryEvidenceType.EXPERIMENTAL,
        atoms=[
            GeometryAtom(id=identifier[label], element=atom_element_map[label], role="center" if label == centre else "ligand")
            for label in ordered
        ],
        bonds=bonds,
        bond_lengths=bond_lengths,
        bond_angles=bond_angles,
        dihedrals=dihedrals,
        coordinates=parsed_coordinates,
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
