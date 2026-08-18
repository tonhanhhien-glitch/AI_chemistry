"""Read/write/merge the admin override file layered on top of the baseline
curated JSON data files.

The effective catalog for each of the baseline loaders the admin page can
affect (curated molecules, experimental geometries, curated properties) is:
baseline entries, with any entry sharing a key replaced by the matching
override entry, plus any override entry whose key has no baseline
counterpart appended at the end.

Deliberately dependency-free with respect to the domain modules that use it
(``molecule_resolver``, the NIST CCCBDB provider, the curated property
provider) so those modules can import this one without a circular import
back from here.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from app.core.config import settings

_OVERRIDES_FILENAME = "molecule_catalog_overrides.json"


def _overrides_path() -> Path:
    return settings.DATA_DIR.resolve() / _OVERRIDES_FILENAME


def load_overrides() -> dict[str, Any]:
    """The admin override document, or an empty-but-shaped one if none exists yet."""

    path = _overrides_path()
    if not path.exists():
        return {"schema_version": "1.0", "molecules": [], "experimental_geometries": [], "properties": {}}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    data.setdefault("schema_version", "1.0")
    data.setdefault("molecules", [])
    data.setdefault("experimental_geometries", [])
    data.setdefault("properties", {})
    return data


def save_overrides(data: dict[str, Any]) -> None:
    """Atomic whole-document write: a crash mid-write can never leave a half-written
    or corrupt override file behind."""

    path = _overrides_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=".molecule_catalog_overrides-", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def merge_by_id(baseline: list[dict[str, Any]], overrides: list[dict[str, Any]], *, key: str = "id") -> list[dict[str, Any]]:
    if not overrides:
        return baseline
    override_by_key = {item[key]: item for item in overrides if key in item}
    merged = [override_by_key.get(item.get(key), item) for item in baseline]
    seen = {item.get(key) for item in baseline}
    merged.extend(item for item in overrides if item.get(key) not in seen)
    return merged


def merge_geometry_records(baseline: list[dict[str, Any]], overrides: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge experimental-geometry records, keyed on the molecule they describe.

    A plain id-merge is not enough here: an admin override's ``id`` (``admin-<mol
    id>``) never collides with a baseline NIST record's own id, so both would survive
    into the same list and match the same identity. The geometry matcher then sees two
    records for one species, calls it ambiguous, and returns neither -- silently
    losing the experimental structure. Any baseline record whose
    ``identity.curated_molecule_id`` an override also claims is dropped first, so an
    admin edit *replaces* the baseline geometry for that molecule rather than shadowing
    it ambiguously.
    """

    if not overrides:
        return baseline
    override_molecule_ids = {
        item.get("identity", {}).get("curated_molecule_id")
        for item in overrides
        if item.get("identity", {}).get("curated_molecule_id")
    }
    filtered_baseline = [
        item for item in baseline
        if item.get("identity", {}).get("curated_molecule_id") not in override_molecule_ids
    ]
    return merge_by_id(filtered_baseline, overrides)


def merge_properties(baseline: dict[str, list[Any]], overrides: dict[str, list[Any]]) -> dict[str, list[Any]]:
    if not overrides:
        return baseline
    merged = dict(baseline)
    merged.update(overrides)
    return merged
