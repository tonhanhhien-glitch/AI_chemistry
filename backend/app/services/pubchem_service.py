"""Typed PubChem formula resolution and 3D retrieval with bounded retry/cache."""

from __future__ import annotations

import hashlib
import json
import logging
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
from app.services.formula_parser import ParsedFormula, parse_formula
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


def _request_bytes(url: str) -> tuple[bytes | None, ExternalServiceState]:
    retries = max(int(settings.PUBCHEM_RETRY_COUNT), 0)
    for attempt in range(retries + 1):
        try:
            _throttle()
            request = Request(url, headers={"User-Agent": "VSEPR-AI/1.0 educational-app"})
            with urlopen(request, timeout=settings.PUBCHEM_TIMEOUT_SECONDS) as response:
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
                time.sleep(min(0.25 * (2**attempt), 1.0))
                continue
            return None, state
        except (TimeoutError, socket.timeout):
            return None, ExternalServiceState.TIMEOUT
        except (URLError, OSError):
            if attempt < retries:
                time.sleep(min(0.25 * (2**attempt), 1.0))
                continue
            return None, ExternalServiceState.TEMPORARY_FAILURE
    return None, ExternalServiceState.TEMPORARY_FAILURE


def _status(state: ExternalServiceState, *, cache_hit: bool = False, message: str | None = None) -> ExternalServiceStatus:
    return ExternalServiceStatus(service="PubChem", state=state, cache_hit=cache_hit, message=message)


def _candidate_from_row(row: dict[str, Any], parsed: ParsedFormula, timestamp: datetime) -> PubChemCandidate | None:
    try:
        candidate_formula = str(row["MolecularFormula"])
        candidate_parsed = parse_formula(candidate_formula)
        charge = int(row.get("Charge", 0))
        covalent_units = int(row["CovalentUnitCount"]) if row.get("CovalentUnitCount") is not None else None
        smiles = row.get("ConnectivitySMILES") or row.get("CanonicalSMILES")
        if candidate_parsed.atoms != parsed.atoms or charge != parsed.charge:
            return None
        if covalent_units is not None and covalent_units != 1:
            return None
        if smiles and "." in str(smiles):
            return None
        cid = int(row["CID"])
        title = str(row.get("Title") or row.get("IUPACName") or f"PubChem CID {cid}")
        return PubChemCandidate(
            id=f"pubchem:{cid}",
            cid=cid,
            formula=parsed.formula,
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


def lookup_pubchem_formula(parsed: ParsedFormula) -> PubChemLookupResult:
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
    raw, state = _request_bytes(url)
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


def lookup_pubchem(query: str) -> list[PubChemCandidate]:
    """Backward-compatible list API; production code uses the typed result."""

    try:
        return lookup_pubchem_formula(parse_formula(query)).candidates
    except ValueError:
        return []


def fetch_pubchem_3d(cid: int) -> PubChemStructureResult:
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
    raw, state = _request_bytes(url)
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
