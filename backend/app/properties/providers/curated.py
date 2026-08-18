"""Locally curated physical/chemical properties, sourced offline from
``app/data/curated_properties.json``.

Unlike :class:`~app.properties.providers.computed.ComputedPropertyProvider` (which
derives values from the resolved record) this provider carries externally sourced
facts -- melting points, appearance, solubility and the like -- that were verified
against PubChem PUG-View and the NIST Chemistry WebBook at curation time, with full
provenance kept on each entry. It sits ahead of the PubChem providers in
``app/properties/service.py`` so a verified local value is never overwritten by a
live lookup, and it needs no network access, so it is available offline.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from app.properties.providers.base import PropertyProviderResult, PropertyQuery
from app.properties.schema import NormalizedProperty, PropertyProviderStatus
from app.services.molecule_overrides import load_overrides, merge_properties
from app.utils.file_loader import load_json

_DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "curated_properties.json"


@lru_cache(maxsize=1)
def _catalog() -> dict[str, tuple[NormalizedProperty, ...]]:
    payload = load_json(_DATA_FILE)
    raw = payload.get("properties")
    if not isinstance(raw, dict):
        raise ValueError("curated_properties.json must contain a 'properties' object")
    raw = merge_properties(raw, load_overrides().get("properties", {}))
    catalog: dict[str, tuple[NormalizedProperty, ...]] = {}
    for species_key, items in raw.items():
        if not isinstance(items, list):
            raise ValueError(f"curated_properties.json entry '{species_key}' must be a list")
        catalog[species_key] = tuple(NormalizedProperty.model_validate(item) for item in items)
    return catalog


def _species_key(formula: str, charge: int) -> str:
    return f"{formula}|{charge}"


class CuratedPropertyProvider:
    """Verified local properties for the 19 curated teaching species. Always available."""

    name = "curated"
    service = "Curated local properties"

    def fetch(self, query: PropertyQuery) -> PropertyProviderResult:
        properties = _catalog().get(_species_key(query.formula, query.charge), ())
        return PropertyProviderResult(
            properties,
            PropertyProviderStatus(provider=self.name, service=self.service, state="success"),
        )
