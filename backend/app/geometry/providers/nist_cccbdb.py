"""NIST CCCBDB experimental geometry, served cache-first.

Priority inside this provider:

1. the reviewed local snapshot shipped in ``app/data/experimental_geometries.json``,
2. the runtime cache of previously normalised CCCBDB fetches,
3. a live CCCBDB fetch (only when ``ENABLE_NIST_CCCBDB`` is set), normalised by
   :mod:`app.geometry.adapters.nist_cccbdb_adapter` and written back to the cache.

Step 3 is what makes a newly supported molecule stop needing a source-code edit:
the first successful fetch persists a normalised record that later requests read
from disk. A CCCBDB outage returns a typed miss, never an exception.
"""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.core.config import settings
from app.geometry.adapters.nist_cccbdb_adapter import (
    NIST_SERVICE_NAME,
    cccbdb_url,
    fetch_cccbdb_geometry_html,
    parse_cccbdb_geometry_html,
)
from app.geometry.providers.base import GeometryProviderResult, GeometryQuery, provider_status
from app.schemas.geometry_evidence_schema import GeometryIdentity, MolecularGeometryEvidence
from app.schemas.molecule_schema import ExternalServiceState
from app.services.molecule_overrides import load_overrides, merge_geometry_records
from app.utils.file_loader import load_json
from app.utils.json_utils import read_json_cache, write_json_cache

logger = logging.getLogger(__name__)

_SNAPSHOT_FILE = Path(__file__).resolve().parents[2] / "data" / "experimental_geometries.json"
_LOCAL_SERVICE = "Local geometry snapshot"


@lru_cache(maxsize=1)
def snapshot_records() -> tuple[MolecularGeometryEvidence, ...]:
    """The reviewed local experimental geometries, validated at load time."""

    payload = load_json(_SNAPSHOT_FILE)
    raw_records = merge_geometry_records(list(payload.get("records", [])), load_overrides().get("experimental_geometries", []))
    records = tuple(MolecularGeometryEvidence.model_validate(item) for item in raw_records)
    if not records:
        raise ValueError("experimental_geometries.json contains no records")
    return records


def _cache_path() -> Path:
    return settings.CACHE_DIR / "nist_geometry_cache.json"


def _cache_key(query: GeometryQuery) -> str:
    return f"{query.inchikey or query.cas_rn or query.formula}:{query.charge}".casefold()


def _identity_matches(identity: GeometryIdentity, query: GeometryQuery) -> bool:
    """Match on the strongest identifier available; fall back to formula only when safe."""

    if identity.charge != query.charge:
        return False
    if query.inchikey and identity.inchikey:
        return identity.inchikey == query.inchikey
    if query.cas_rn and identity.cas_rn:
        return identity.cas_rn == query.cas_rn
    if query.canonical_identity and identity.canonical_identity:
        return identity.canonical_identity == query.canonical_identity
    if query.curated_molecule_id and identity.curated_molecule_id:
        return identity.curated_molecule_id == query.curated_molecule_id
    return bool(
        identity.formula_identity_unambiguous
        and identity.formula == query.formula
        and (not query.atom_inventory or identity.atom_inventory == query.atom_inventory)
    )


def _select(records: tuple[MolecularGeometryEvidence, ...], query: GeometryQuery) -> MolecularGeometryEvidence | None:
    """One unambiguous match, or nothing. Two matches mean the identity is not pinned."""

    matches = [record for record in records if _identity_matches(record.identity, query)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        logger.info("Ambiguous experimental geometry match for %s; refusing to guess", query.formula)
    return None


def _cached_records() -> tuple[MolecularGeometryEvidence, ...]:
    cache = read_json_cache(_cache_path())
    now = time.time()
    records: list[MolecularGeometryEvidence] = []
    for entry in cache.values():
        if not isinstance(entry, dict):
            continue
        if now - float(entry.get("cached_at", 0)) > settings.NIST_CACHE_TTL_SECONDS:
            continue
        try:
            records.append(MolecularGeometryEvidence.model_validate(entry["evidence"]))
        except (KeyError, TypeError, ValidationError):
            continue
    return tuple(records)


def _store(query: GeometryQuery, evidence: MolecularGeometryEvidence) -> None:
    path = _cache_path()
    cache = read_json_cache(path)
    cache[_cache_key(query)] = {
        "cached_at": time.time(),
        "evidence": evidence.model_dump(mode="json"),
    }
    write_json_cache(path, cache)


def _query_identity(query: GeometryQuery) -> GeometryIdentity:
    return GeometryIdentity(
        formula=query.formula,
        charge=query.charge,
        atom_inventory=dict(query.atom_inventory),
        inchi=query.inchi,
        inchikey=query.inchikey,
        cas_rn=query.cas_rn,
        pubchem_cid=query.pubchem_cid,
        canonical_identity=query.canonical_identity,
        curated_molecule_id=query.curated_molecule_id,
        formula_identity_unambiguous=False,
    )


class NistCccbdbProvider:
    """Experimental gas-phase geometry from NIST CCCBDB, snapshot- and cache-first."""

    name = "nist_cccbdb"
    service = NIST_SERVICE_NAME

    def fetch(self, query: GeometryQuery) -> GeometryProviderResult:
        local = _select(snapshot_records(), query)
        if local is not None:
            return GeometryProviderResult(local, provider_status(_LOCAL_SERVICE, ExternalServiceState.CACHE_HIT, cache_hit=True))

        cached = _select(_cached_records(), query)
        if cached is not None:
            return GeometryProviderResult(cached, provider_status(self.service, ExternalServiceState.CACHE_HIT, cache_hit=True))

        if not settings.ENABLE_NIST_CCCBDB:
            return GeometryProviderResult(None, provider_status(self.service, ExternalServiceState.DISABLED))

        cas_rn = query.cas_rn
        if not cas_rn:
            from app.services.chemical_query_resolver import cas_for_identity
            cas_rn = cas_for_identity(query.formula, query.charge)
        if not cas_rn and query.pubchem_cid and settings.ENABLE_PUBCHEM:
            from app.services.pubchem_service import fetch_pubchem_cas_rn
            cas_rn = fetch_pubchem_cas_rn(int(query.pubchem_cid), timeout=query.timeout)

        if not cas_rn:
            return GeometryProviderResult(None, provider_status(
                self.service, ExternalServiceState.NOT_FOUND,
                message="CCCBDB is addressed by CAS number; none was resolved for this identity.",
            ))

        html, state = fetch_cccbdb_geometry_html(cas_rn, charge=query.charge, timeout=query.timeout)
        if html is None:
            logger.info("CCCBDB geometry fetch ended with state=%s", state.value)
            return GeometryProviderResult(None, provider_status(self.service, state))
        evidence = parse_cccbdb_geometry_html(
            html,
            identity=_query_identity(query),
            source_url=cccbdb_url(cas_rn, query.charge),
            retrieved_at=datetime.now(UTC),
        )
        if evidence is None:
            return GeometryProviderResult(None, provider_status(
                self.service, ExternalServiceState.INVALID_RESPONSE,
                message="The CCCBDB page held no complete geometry for this species.",
            ))
        _store(query, evidence)
        return GeometryProviderResult(evidence, provider_status(self.service, ExternalServiceState.SUCCESS))


NistCccbdbGeometryProvider = NistCccbdbProvider


def snapshot_identity_payloads() -> list[dict[str, Any]]:
    """Identity rows for the local snapshot; used by name/formula resolution."""

    return [record.identity.model_dump(mode="json") for record in snapshot_records()]
