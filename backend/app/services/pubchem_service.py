"""Typed PubChem formula resolution and 3D retrieval with bounded retry/cache."""

from __future__ import annotations

import hashlib
import json
import logging
import re
import socket
import threading
import time
from datetime import UTC, datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from pydantic import BaseModel, Field

from app.core.config import settings
from app.schemas.molecule_schema import (
    ExternalServiceState,
    ExternalServiceStatus,
    PubChemCandidate,
)
from app.services.formula_parser import ParsedFormula, canonical_formula, parse_formula
from app.utils.json_utils import read_json_cache, write_json_cache

logger = logging.getLogger(__name__)
_PROPERTY_FIELDS = (
    "CID,MolecularFormula,Charge,Title,IUPACName,ConnectivitySMILES,"
    "CanonicalSMILES,IsomericSMILES,InChI,InChIKey,MolecularWeight,"
    "CovalentUnitCount"
)
_RATE_LOCK = threading.Lock()
_LAST_REQUEST_AT = 0.0


class PubChemLookupResult(BaseModel):
    candidates: list[PubChemCandidate] = Field(default_factory=list)
    status: ExternalServiceStatus
    rejected_count: int = 0


class PubChemStructureResult(BaseModel):
    data: str | None = None
    status: ExternalServiceStatus


def _cache_timestamp() -> datetime:
    return datetime.now(UTC)


def _formula_body(formula: str) -> str:
    if "^" in formula:
        return formula.split("^", 1)[0]
    return formula[:-1] if formula.endswith(("+", "-")) else formula


def _throttle() -> None:
    global _LAST_REQUEST_AT
    rate = max(float(settings.PUBCHEM_MAX_REQUESTS_PER_SECOND), 0.1)
    minimum_interval = 1.0 / rate
    with _RATE_LOCK:
        wait = minimum_interval - (time.monotonic() - _LAST_REQUEST_AT)
        if wait > 0:
            time.sleep(wait)
        _LAST_REQUEST_AT = time.monotonic()


def _request_bytes(url: str, *, timeout: float | None = None, deadline: float | None = None) -> tuple[bytes | None, ExternalServiceState]:
    retries = max(int(settings.PUBCHEM_RETRY_COUNT), 0)
    for attempt in range(retries + 1):
        now = time.monotonic()
        if deadline is not None and now >= deadline:
            return None, ExternalServiceState.TIMEOUT
        remaining = (deadline - now) if deadline is not None else None
        effective_timeout = settings.PUBCHEM_TIMEOUT_SECONDS if timeout is None else min(settings.PUBCHEM_TIMEOUT_SECONDS, timeout)
        if remaining is not None:
            effective_timeout = min(effective_timeout, remaining)
        if effective_timeout <= 0:
            return None, ExternalServiceState.TIMEOUT

        try:
            _throttle()
            request = Request(url, headers={"User-Agent": "VSEPR-AI/1.0 educational-app"})
            with urlopen(request, timeout=effective_timeout) as response:
                return response.read(), ExternalServiceState.SUCCESS
        except HTTPError as exc:
            if exc.code in {400, 404}:
                return None, ExternalServiceState.NOT_FOUND
            if exc.code == 429:
                state = ExternalServiceState.RATE_LIMITED
            elif exc.code == 503 or 500 <= exc.code < 600:
                state = ExternalServiceState.TEMPORARY_FAILURE
            else:
                return None, ExternalServiceState.INVALID_RESPONSE
            if attempt < retries:
                sleep_time = min(0.25 * (2**attempt), 1.0)
                if deadline is not None and time.monotonic() + sleep_time >= deadline:
                    return None, ExternalServiceState.TIMEOUT
                time.sleep(sleep_time)
                continue
            return None, state
        except (TimeoutError, socket.timeout):
            return None, ExternalServiceState.TIMEOUT
        except (URLError, OSError):
            if attempt < retries:
                sleep_time = min(0.25 * (2**attempt), 1.0)
                if deadline is not None and time.monotonic() + sleep_time >= deadline:
                    return None, ExternalServiceState.TIMEOUT
                time.sleep(sleep_time)
                continue
            return None, ExternalServiceState.TEMPORARY_FAILURE
    return None, ExternalServiceState.TEMPORARY_FAILURE


def _status(state: ExternalServiceState, *, cache_hit: bool = False, message: str | None = None) -> ExternalServiceStatus:
    return ExternalServiceStatus(service="PubChem", state=state, cache_hit=cache_hit, message=message)


def _candidate_from_row(row: dict[str, Any], parsed: ParsedFormula | None, timestamp: datetime) -> PubChemCandidate | None:
    """Validate one PubChem row into a typed candidate, or reject it.

    ``parsed`` is the formula the caller asked for. A name lookup has no expected
    formula, so it passes ``None`` and the row's own formula is validated against the
    supported grammar and element scope instead.
    """

    try:
        candidate_formula = str(row["MolecularFormula"])
        candidate_parsed = parse_formula(candidate_formula)
        charge = int(row.get("Charge", 0))
        covalent_units = int(row["CovalentUnitCount"]) if row.get("CovalentUnitCount") is not None else None
        smiles = row.get("ConnectivitySMILES") or row.get("CanonicalSMILES")
        if parsed is not None and (candidate_parsed.atoms != parsed.atoms or charge != parsed.charge):
            return None
        if covalent_units is not None and covalent_units != 1:
            return None
        if smiles and "." in str(smiles):
            return None
        cid = int(row["CID"])
        title = str(row.get("Title") or row.get("IUPACName") or f"PubChem CID {cid}")
        # PubChem answers in Hill notation; render the inventory in this app's
        # conventional order so one substance has one spelling everywhere.
        resolved_formula = parsed.formula if parsed is not None else canonical_formula(candidate_parsed.atoms, charge)
        return PubChemCandidate(
            id=f"pubchem:{cid}",
            cid=cid,
            formula=resolved_formula,
            charge=charge,
            name_vi=title,
            name_en=title,
            canonical_smiles=str(smiles) if smiles else None,
            isomeric_smiles=str(row.get("SMILES") or row.get("IsomericSMILES")) if row.get("SMILES") or row.get("IsomericSMILES") else None,
            inchi=str(row["InChI"]) if row.get("InChI") else None,
            inchikey=str(row["InChIKey"]) if row.get("InChIKey") else None,
            molecular_weight=str(row["MolecularWeight"]) if row.get("MolecularWeight") is not None else None,
            title=title,
            iupac_name=str(row["IUPACName"]) if row.get("IUPACName") else None,
            covalent_unit_count=covalent_units,
            cache_timestamp=timestamp,
        )
    except (KeyError, TypeError, ValueError):
        return None


def _call_request_bytes(url: str, *, timeout: float | None = None, deadline: float | None = None) -> tuple[bytes | None, ExternalServiceState]:
    try:
        return _request_bytes(url, timeout=timeout, deadline=deadline)
    except TypeError:
        try:
            return _request_bytes(url, timeout=timeout)
        except TypeError:
            return _request_bytes(url)


def lookup_pubchem_formula(parsed: ParsedFormula, *, timeout: float | None = None) -> PubChemLookupResult:
    """Resolve a formula without accepting an unvalidated first PubChem match."""

    if not settings.ENABLE_PUBCHEM:
        return PubChemLookupResult(status=_status(ExternalServiceState.DISABLED))
    key_source = f"formula:{parsed.formula}:{parsed.charge}".casefold()
    key = hashlib.sha256(key_source.encode("utf-8")).hexdigest()
    cache_path = settings.CACHE_DIR / "pubchem_identity_cache.json"
    cache = read_json_cache(cache_path)
    cached = cache.get(key)
    now = time.time()
    if isinstance(cached, dict) and now - float(cached.get("cached_at", 0)) <= settings.PUBCHEM_CACHE_TTL_SECONDS:
        try:
            candidates = [PubChemCandidate.model_validate(item) for item in cached.get("candidates", [])]
            return PubChemLookupResult(candidates=candidates, status=_status(ExternalServiceState.CACHE_HIT, cache_hit=True))
        except (TypeError, ValueError):
            cache.pop(key, None)

    formula = quote(_formula_body(parsed.formula), safe="")
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/fastformula/{formula}/property/{_PROPERTY_FIELDS}/JSON"
    raw, state = _call_request_bytes(url, timeout=timeout)
    if raw is None:
        logger.info("PubChem formula lookup ended with state=%s", state.value)
        return PubChemLookupResult(status=_status(state))
    try:
        payload = json.loads(raw.decode("utf-8"))
        rows = payload.get("PropertyTable", {}).get("Properties", [])
        if not isinstance(rows, list):
            raise ValueError("Properties is not a list")
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, AttributeError):
        logger.warning("PubChem returned an invalid formula response")
        return PubChemLookupResult(status=_status(ExternalServiceState.INVALID_RESPONSE))

    timestamp = _cache_timestamp()
    candidates: list[PubChemCandidate] = []
    for row in rows[: settings.PUBCHEM_MAX_CANDIDATES]:
        if isinstance(row, dict):
            candidate = _candidate_from_row(row, parsed, timestamp)
            if candidate is not None:
                candidates.append(candidate)
    unique = {candidate.cid: candidate for candidate in candidates}
    candidates = list(unique.values())
    rejected = len(rows) - len(candidates)
    if not candidates:
        state = ExternalServiceState.FORMULA_MISMATCH if rows else ExternalServiceState.NOT_FOUND
    elif len(candidates) > 1:
        state = ExternalServiceState.AMBIGUOUS
    else:
        state = ExternalServiceState.SUCCESS
    cache[key] = {
        "cached_at": now,
        "candidates": [candidate.model_dump(mode="json") for candidate in candidates],
    }
    write_json_cache(cache_path, cache)
    return PubChemLookupResult(candidates=candidates, status=_status(state), rejected_count=max(rejected, 0))


def lookup_pubchem_name(name: str, *, timeout: float | None = None) -> PubChemLookupResult:
    """Resolve a chemical name or alias to validated PubChem candidates.

    Rows are accepted only when their own formula parses under the supported grammar
    and element scope and they describe a single covalent unit, so a name that maps to
    a salt, a hydrate or an out-of-scope element yields no candidate rather than a
    plausible-looking wrong one. Chemically distinct survivors are all returned; the
    caller decides, and must not silently take the first.
    """

    if not settings.ENABLE_PUBCHEM:
        return PubChemLookupResult(status=_status(ExternalServiceState.DISABLED))
    normalized = name.strip()
    if not normalized:
        return PubChemLookupResult(status=_status(ExternalServiceState.NOT_FOUND))
    key = hashlib.sha256(f"name:{normalized}".casefold().encode("utf-8")).hexdigest()
    cache_path = settings.CACHE_DIR / "pubchem_identity_cache.json"
    cache = read_json_cache(cache_path)
    cached = cache.get(key)
    now = time.time()
    if isinstance(cached, dict) and now - float(cached.get("cached_at", 0)) <= settings.PUBCHEM_CACHE_TTL_SECONDS:
        try:
            candidates = [PubChemCandidate.model_validate(item) for item in cached.get("candidates", [])]
            return PubChemLookupResult(candidates=candidates, status=_status(ExternalServiceState.CACHE_HIT, cache_hit=True))
        except (TypeError, ValueError):
            cache.pop(key, None)

    url = (
        f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{quote(normalized, safe='')}"
        f"/property/{_PROPERTY_FIELDS}/JSON"
    )
    raw, state = _call_request_bytes(url, timeout=timeout)
    if raw is None:
        logger.info("PubChem name lookup ended with state=%s", state.value)
        return PubChemLookupResult(status=_status(state))
    try:
        payload = json.loads(raw.decode("utf-8"))
        rows = payload.get("PropertyTable", {}).get("Properties", [])
        if not isinstance(rows, list):
            raise ValueError("Properties is not a list")
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, AttributeError):
        logger.warning("PubChem returned an invalid name response")
        return PubChemLookupResult(status=_status(ExternalServiceState.INVALID_RESPONSE))

    timestamp = _cache_timestamp()
    candidates: list[PubChemCandidate] = []
    for row in rows[: settings.PUBCHEM_MAX_CANDIDATES]:
        if isinstance(row, dict):
            candidate = _candidate_from_row(row, None, timestamp)
            if candidate is not None:
                candidates.append(candidate)
    # Two CIDs describing the same substance are one answer, not an ambiguity.
    distinct: dict[tuple[str, int, str | None], PubChemCandidate] = {}
    for candidate in candidates:
        distinct.setdefault((candidate.formula, candidate.charge, candidate.inchikey), candidate)
    candidates = list(distinct.values())
    if not candidates:
        state = ExternalServiceState.FORMULA_MISMATCH if rows else ExternalServiceState.NOT_FOUND
    elif len(candidates) > 1:
        state = ExternalServiceState.AMBIGUOUS
    else:
        state = ExternalServiceState.SUCCESS
    cache[key] = {"cached_at": now, "candidates": [candidate.model_dump(mode="json") for candidate in candidates]}
    write_json_cache(cache_path, cache)
    return PubChemLookupResult(candidates=candidates, status=_status(state))


def lookup_pubchem_cid(cid: int, *, timeout: float | None = None) -> PubChemCandidate | None:
    """Directly fetch a validated PubChemCandidate by CID without formula search."""
    if not settings.ENABLE_PUBCHEM:
        return None
    key = f"cid:{cid}"
    cache_path = settings.CACHE_DIR / "pubchem_identity_cache.json"
    cache = read_json_cache(cache_path)
    cached = cache.get(key)
    now = time.time()
    if isinstance(cached, dict) and now - float(cached.get("cached_at", 0)) <= settings.PUBCHEM_CACHE_TTL_SECONDS:
        cand_dict = cached.get("candidate")
        if isinstance(cand_dict, dict):
            try:
                return PubChemCandidate.model_validate(cand_dict)
            except (TypeError, ValueError):
                cache.pop(key, None)

    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/property/{_PROPERTY_FIELDS}/JSON"
    raw, state = _call_request_bytes(url, timeout=timeout)
    if raw is None:
        return None
    try:
        payload = json.loads(raw.decode("utf-8"))
        rows = payload.get("PropertyTable", {}).get("Properties", [])
        if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
            return None
        timestamp = _cache_timestamp()
        candidate = _candidate_from_row(rows[0], None, timestamp)
        if candidate is not None:
            cache[key] = {"cached_at": now, "candidate": candidate.model_dump(mode="json")}
            write_json_cache(cache_path, cache)
        return candidate
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, AttributeError):
        return None


def is_valid_cas_rn(cas: str) -> bool:
    """Validate CAS Registry Number format and checksum."""
    parts = cas.split("-")
    if len(parts) != 3:
        return False
    if not (2 <= len(parts[0]) <= 7 and len(parts[1]) == 2 and len(parts[2]) == 1):
        return False
    if not (parts[0].isdigit() and parts[1].isdigit() and parts[2].isdigit()):
        return False
    digits = parts[0] + parts[1]
    check_digit = int(parts[2])
    total = sum(int(d) * (len(digits) - i) for i, d in enumerate(digits))
    return total % 10 == check_digit


def fetch_pubchem_cas_rn(cid: int, *, timeout: float | None = None) -> str | None:
    """Fetch CAS Registry Number for a PubChem CID from its synonyms."""
    if not settings.ENABLE_PUBCHEM:
        return None
    cache_path = settings.CACHE_DIR / "pubchem_cas_cache.json"
    cache = read_json_cache(cache_path)
    key = str(cid)
    now = time.time()
    cached = cache.get(key)
    if isinstance(cached, dict) and now - float(cached.get("cached_at", 0)) <= settings.PUBCHEM_CACHE_TTL_SECONDS:
        cas_val = cached.get("cas_rn")
        if isinstance(cas_val, str) and cas_val:
            return cas_val
        if cached.get("not_found"):
            return None

    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/synonyms/JSON"
    raw, state = _call_request_bytes(url, timeout=timeout)
    if raw is None:
        return None
    try:
        payload = json.loads(raw.decode("utf-8"))
        info_list = payload.get("InformationList", {}).get("Information", [])
        if not info_list or not isinstance(info_list[0], dict):
            return None
        synonyms = info_list[0].get("Synonym", [])
        if not isinstance(synonyms, list):
            return None
        cas_pattern = re.compile(r"^\d{2,7}-\d{2}-\d$")
        found_cas: str | None = None
        for syn in synonyms:
            if isinstance(syn, str) and cas_pattern.match(syn.strip()) and is_valid_cas_rn(syn.strip()):
                found_cas = syn.strip()
                break
        cache[key] = {"cached_at": now, "cas_rn": found_cas, "not_found": found_cas is None}
        write_json_cache(cache_path, cache)
        return found_cas
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, AttributeError):
        return None


def lookup_pubchem(query: str) -> list[PubChemCandidate]:
    """Backward-compatible list API; production code uses the typed result."""

    try:
        return lookup_pubchem_formula(parse_formula(query)).candidates
    except ValueError:
        return []


def fetch_pubchem_2d(cid: int, *, timeout: float | None = None) -> PubChemStructureResult:
    """Fetch 2D SDF/molfile connectivity from PubChem."""
    if not settings.ENABLE_PUBCHEM:
        return PubChemStructureResult(status=_status(ExternalServiceState.DISABLED))
    cache_path = settings.CACHE_DIR / "pubchem_structure_cache.json"
    cache = read_json_cache(cache_path)
    key = f"{cid}:2d:sdf"
    now = time.time()
    cached = cache.get(key)
    if isinstance(cached, dict) and now - float(cached.get("cached_at", 0)) <= settings.PUBCHEM_CACHE_TTL_SECONDS:
        data = cached.get("data")
        if isinstance(data, str) and data.strip():
            return PubChemStructureResult(data=data, status=_status(ExternalServiceState.CACHE_HIT, cache_hit=True))
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF?record_type=2d"
    raw, state = _call_request_bytes(url, timeout=timeout)
    if raw is None:
        if state is ExternalServiceState.NOT_FOUND:
            state = ExternalServiceState.CONFORMER_UNAVAILABLE
        return PubChemStructureResult(status=_status(state))
    try:
        data = raw.decode("utf-8")
        if "V2000" not in data and "V3000" not in data:
            raise ValueError("not a molfile")
    except (UnicodeDecodeError, ValueError):
        return PubChemStructureResult(status=_status(ExternalServiceState.INVALID_RESPONSE))
    cache[key] = {"cached_at": now, "data": data}
    write_json_cache(cache_path, cache)
    return PubChemStructureResult(data=data, status=_status(ExternalServiceState.SUCCESS))


def fetch_pubchem_3d(cid: int, *, timeout: float | None = None) -> PubChemStructureResult:
    if not settings.ENABLE_PUBCHEM:
        return PubChemStructureResult(status=_status(ExternalServiceState.DISABLED))
    cache_path = settings.CACHE_DIR / "pubchem_structure_cache.json"
    cache = read_json_cache(cache_path)
    key = f"{cid}:3d:sdf"
    now = time.time()
    cached = cache.get(key)
    if isinstance(cached, dict) and now - float(cached.get("cached_at", 0)) <= settings.PUBCHEM_CACHE_TTL_SECONDS:
        data = cached.get("data")
        if isinstance(data, str) and data.strip():
            return PubChemStructureResult(data=data, status=_status(ExternalServiceState.CACHE_HIT, cache_hit=True))
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF?record_type=3d"
    raw, state = _call_request_bytes(url, timeout=timeout)
    if raw is None:
        if state is ExternalServiceState.NOT_FOUND:
            state = ExternalServiceState.CONFORMER_UNAVAILABLE
        return PubChemStructureResult(status=_status(state))
    try:
        data = raw.decode("utf-8")
        if "V2000" not in data and "V3000" not in data:
            raise ValueError("not a molfile")
    except (UnicodeDecodeError, ValueError):
        return PubChemStructureResult(status=_status(ExternalServiceState.INVALID_RESPONSE))
    cache[key] = {"cached_at": now, "data": data}
    write_json_cache(cache_path, cache)
    return PubChemStructureResult(data=data, status=_status(ExternalServiceState.SUCCESS))
