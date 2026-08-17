"""One entry point for whatever a student types.

The frontend used to guess: an input starting with an uppercase letter was treated as
a formula, anything else as a name. That misroutes ``sulfate`` (lowercase, but only
resolvable as a name) and ``Sulfate`` (uppercase, but not a formula) alike, and it put
a chemistry decision in React.

Resolution order:

1. strict formula parsing -- if the *whole* query is a valid formula, that is the answer;
2. otherwise treat it as a name or alias and search the local curated identities;
3. otherwise query PubChem by name, validating the returned formula, charge, element
   scope and single-covalent-unit connectivity;
4. if chemically distinct candidates remain, return them all as typed candidates. The
   first PubChem hit is never silently chosen.
"""

from __future__ import annotations

import logging
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from app.core.exceptions import (
    AmbiguousMoleculeError,
    FormulaParseError,
    UnsupportedMoleculeError,
)
from app.schemas.molecule_schema import ExternalServiceState, ExternalServiceStatus, PubChemCandidate
from app.services.formula_parser import ParsedFormula, parse_formula
from app.services.pubchem_service import lookup_pubchem_name
from app.utils.file_loader import load_json

logger = logging.getLogger(__name__)

_DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "chemical_identities.json"

QueryKind = Literal["formula", "name"]


@dataclass(frozen=True, slots=True)
class LocalIdentity:
    formula: str
    charge: int
    curated_molecule_id: str | None
    cas_rn: str | None
    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class QueryResolution:
    """What the query turned out to mean."""

    raw: str
    kind: QueryKind
    parsed: ParsedFormula
    molecule_id: str | None = None
    pubchem_cid: int | None = None
    cas_rn: str | None = None
    matched_name: str | None = None
    candidate: PubChemCandidate | None = None
    """The already-validated PubChem candidate, so the identity is not looked up twice."""
    statuses: tuple[ExternalServiceStatus, ...] = field(default=())


def _normalize(value: str) -> str:
    """Casefold and strip accents so ``Nước``, ``nuoc`` and ``nước`` all match."""

    decomposed = unicodedata.normalize("NFD", value.strip().casefold())
    stripped = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return " ".join(stripped.replace("-", " ").split())


@lru_cache(maxsize=1)
def local_identities() -> tuple[LocalIdentity, ...]:
    payload = load_json(_DATA_FILE)
    return tuple(
        LocalIdentity(
            formula=str(item["formula"]),
            charge=int(item.get("charge", 0)),
            curated_molecule_id=item.get("curated_molecule_id"),
            cas_rn=item.get("cas_rn"),
            names=tuple(str(name) for name in item.get("names", [])),
        )
        for item in payload.get("identities", [])
    )


def cas_for_identity(formula: str, charge: int) -> str | None:
    """CAS registry number for a formula/charge, used to address NIST CCCBDB."""

    for identity in local_identities():
        if identity.formula == formula and identity.charge == charge:
            return identity.cas_rn
    return None


def _local_name_matches(query: str) -> list[LocalIdentity]:
    needle = _normalize(query)
    if not needle:
        return []
    exact = [identity for identity in local_identities() if any(_normalize(name) == needle for name in identity.names)]
    if exact:
        return exact
    from app.services.molecule_resolver import curated_records

    matches: list[LocalIdentity] = []
    for record in curated_records():
        haystack = [record["name_vi"], record["name_en"], *record.get("aliases", [])]
        if any(_normalize(value) == needle for value in haystack):
            matches.append(LocalIdentity(
                formula=record["formula"], charge=int(record["charge"]),
                curated_molecule_id=record["id"], cas_rn=None, names=(needle,),
            ))
    return matches


def _candidate_payload(candidate: PubChemCandidate) -> dict[str, Any]:
    return {
        **candidate.model_dump(mode="json"),
        "ax_en": "pending",
        "molecular_geometry": "pending deterministic analysis",
        "molecular_geometry_vi": "đang chờ phân tích tất định",
    }


def resolve_chemical_query(query: str, *, pubchem_cid: int | None = None) -> QueryResolution:
    """Resolve a raw chemical query to a parsed formula plus whatever identity is known.

    Raises :class:`AmbiguousMoleculeError` when several chemically distinct substances
    match, and :class:`UnsupportedMoleculeError` when nothing does.
    """

    raw = (query or "").strip()
    if not raw:
        raise UnsupportedMoleculeError("empty query")

    try:
        parsed = parse_formula(raw)
    except FormulaParseError:
        parsed = None
    if parsed is not None:
        return QueryResolution(
            raw=raw, kind="formula", parsed=parsed,
            cas_rn=cas_for_identity(parsed.formula, parsed.charge),
        )

    local = _local_name_matches(raw)
    distinct = {(identity.formula, identity.charge) for identity in local}
    if len(distinct) == 1:
        identity = local[0]
        return QueryResolution(
            raw=raw, kind="name", parsed=parse_formula(identity.formula),
            molecule_id=identity.curated_molecule_id, cas_rn=identity.cas_rn,
            matched_name=raw,
        )
    if len(distinct) > 1:
        raise AmbiguousMoleculeError([
            {
                "id": identity.curated_molecule_id or f"local:{identity.formula}",
                "formula": identity.formula, "charge": identity.charge,
                "name_vi": identity.names[0] if identity.names else identity.formula,
                "name_en": identity.names[0] if identity.names else identity.formula,
                "source": "Curated identity",
            }
            for identity in local
        ])

    lookup = lookup_pubchem_name(raw)
    statuses = (lookup.status,)
    if not lookup.candidates:
        if lookup.status.state is ExternalServiceState.DISABLED:
            raise UnsupportedMoleculeError(raw)
        raise UnsupportedMoleculeError(raw)

    candidates = lookup.candidates
    if pubchem_cid is not None:
        candidates = [candidate for candidate in candidates if candidate.cid == pubchem_cid]
        if not candidates:
            raise UnsupportedMoleculeError(f"{raw} / PubChem CID {pubchem_cid}")
    if len(candidates) > 1:
        raise AmbiguousMoleculeError([_candidate_payload(candidate) for candidate in candidates])

    candidate = candidates[0]
    return QueryResolution(
        raw=raw, kind="name", parsed=parse_formula(candidate.formula),
        pubchem_cid=candidate.cid, matched_name=candidate.title or raw,
        cas_rn=cas_for_identity(candidate.formula, candidate.charge),
        candidate=candidate, statuses=statuses,
    )
