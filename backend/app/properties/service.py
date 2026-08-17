"""Assemble property bundles from the providers, under a wall-clock budget.

``/analyze`` gets :func:`fast_properties` -- purely local, no network -- so the
deterministic analysis stays responsive. The full table, including PubChem's computed
descriptors and annotation text, is assembled by :func:`full_properties` behind the
dedicated ``/properties`` endpoint, which the frontend calls only when the student
opens the property section.
"""

from __future__ import annotations

import logging
import time

from app.core.config import settings
from app.properties.providers.base import PropertyProvider, PropertyQuery
from app.properties.providers.computed import ComputedPropertyProvider
from app.properties.providers.pubchem_rest import PubChemRestPropertyProvider
from app.properties.providers.pubchem_view import PubChemViewPropertyProvider
from app.properties.schema import NormalizedProperty, PropertyBundle, PropertyProviderStatus

logger = logging.getLogger(__name__)

#: Later providers never overwrite an earlier provider's value for the same key.
_PROVIDER_ORDER: tuple[type[PropertyProvider], ...] = (
    ComputedPropertyProvider,
    PubChemRestPropertyProvider,
    PubChemViewPropertyProvider,
)


def _merge(existing: list[NormalizedProperty], incoming: tuple[NormalizedProperty, ...]) -> None:
    seen = {item.key for item in existing}
    for item in incoming:
        if item.key not in seen:
            existing.append(item)
            seen.add(item.key)


def fast_properties(query: PropertyQuery) -> PropertyBundle:
    """Local, network-free properties for the inline analysis response."""

    provider = ComputedPropertyProvider()
    result = provider.fetch(query)
    return PropertyBundle(
        formula=query.formula, charge=query.charge,
        properties=list(result.properties),
        statuses=[result.status] if result.status else [],
    )


def full_properties(query: PropertyQuery, *, budget_seconds: float | None = None) -> PropertyBundle:
    """Every provider's contribution, bounded by a shared wall-clock budget.

    A provider that fails, times out or is skipped is recorded in ``statuses`` and sets
    ``partial``; the rest of the table is still returned. No provider failure can empty
    the bundle, because the computed provider runs first and never touches the network.
    """

    deadline = time.monotonic() + (
        settings.PROPERTY_EXTERNAL_BUDGET_SECONDS if budget_seconds is None else budget_seconds
    )
    properties: list[NormalizedProperty] = []
    statuses: list[PropertyProviderStatus] = []
    partial = False

    for provider_class in _PROVIDER_ORDER:
        provider = provider_class()
        remaining = deadline - time.monotonic()
        if provider.name != "computed" and remaining <= 0:
            statuses.append(PropertyProviderStatus(
                provider=provider.name, service=provider.service, state="timeout",
                message="Skipped: the property stage exceeded its wall-clock budget.",
            ))
            partial = True
            continue
        try:
            result = provider.fetch(query)
        except Exception:  # noqa: BLE001 - one bad provider must not empty the table
            logger.exception("Property provider %s failed; continuing", provider.name)
            statuses.append(PropertyProviderStatus(
                provider=provider.name, service=provider.service, state="temporary_failure",
            ))
            partial = True
            continue
        _merge(properties, result.properties)
        if result.status is not None:
            statuses.append(result.status)
            if result.status.state not in {"success", "cache_hit", "disabled"}:
                partial = True

    return PropertyBundle(
        formula=query.formula, charge=query.charge,
        properties=properties, statuses=statuses, partial=partial,
    )
