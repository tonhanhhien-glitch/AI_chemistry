"""Experimental-first geometry resolution across all providers.

Priority, highest first:

1. experimental NIST CCCBDB geometry (local snapshot, runtime cache, live fetch),
2. any further experimental provider registered later,
3. a PubChem 3D conformer,
4. an RDKit conformer,
5. the idealized VSEPR model.

Every candidate must survive :func:`app.geometry.fitter.fit_cartesian_coordinates`:
coordinates are produced from the source's constraints and then each constraint is
recomputed from those coordinates. A record whose own numbers cannot be reproduced
is rejected and the next provider is tried, so a bad source degrades to the next
best evidence instead of putting a wrong number on screen.

The whole stage runs under one wall-clock budget. When the budget is exhausted the
resolver stops calling external providers and falls through to the local
idealization, which keeps ``/analyze`` responsive during an outage.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

from app.core.config import settings
from app.geometry.fitter import GeometryFitResult, fit_cartesian_coordinates
from app.geometry.providers.base import GeometryEvidenceProvider, GeometryProviderResult, GeometryQuery, provider_status
from app.geometry.providers.computed import PubChemGeometryProvider, RdkitGeometryProvider
from app.geometry.providers.ideal_vsepr import IdealVseprProvider
from app.geometry.providers.nist_cccbdb import NistCccbdbProvider
from app.schemas.geometry_evidence_schema import GeometryCoordinate, GeometryEvidenceType, MolecularGeometryEvidence
from app.schemas.molecule_schema import ExternalServiceState, ExternalServiceStatus

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ResolvedGeometry:
    """The winning evidence together with the coordinates actually validated from it."""

    evidence: MolecularGeometryEvidence
    coordinates: tuple[GeometryCoordinate, ...]
    fit: GeometryFitResult
    provider_name: str
    statuses: tuple[ExternalServiceStatus, ...] = ()
    rejected: tuple[str, ...] = ()

    @property
    def evidence_type(self) -> GeometryEvidenceType:
        return self.evidence.evidence_type

    @property
    def is_experimental(self) -> bool:
        return self.evidence.is_experimental

    @property
    def is_computed(self) -> bool:
        return self.evidence.evidence_type is GeometryEvidenceType.COMPUTED_CONFORMER

    @property
    def is_ideal(self) -> bool:
        return self.evidence.evidence_type is GeometryEvidenceType.IDEAL_VSEPR


def experimental_providers() -> list[GeometryEvidenceProvider]:
    """Experimental sources, highest priority first. Extend here, not in the services."""

    return [NistCccbdbProvider()]


def computed_providers() -> list[GeometryEvidenceProvider]:
    return [PubChemGeometryProvider(), RdkitGeometryProvider()]


def resolve_geometry(
    query: GeometryQuery,
    *,
    ideal_shape_target_deg: float | None = None,
    ideal_shape_source: str | None = None,
    budget_seconds: float | None = None,
) -> ResolvedGeometry:
    """Resolve the best available geometry for ``query``; never raises for an outage."""

    deadline = time.monotonic() + (
        settings.GEOMETRY_EXTERNAL_BUDGET_SECONDS if budget_seconds is None else budget_seconds
    )
    statuses: list[ExternalServiceStatus] = []
    rejected: list[str] = []

    ordered: list[GeometryEvidenceProvider] = [*experimental_providers(), *computed_providers()]
    for provider in ordered:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            statuses.append(provider_status(
                provider.service, ExternalServiceState.TIMEOUT,
                message="Skipped: the geometry stage exceeded its wall-clock budget.",
            ))
            continue
        try:
            result: GeometryProviderResult = provider.fetch(query.with_timeout(remaining))
        except Exception:  # noqa: BLE001 - a provider must never break local analysis
            logger.exception("Geometry provider %s failed; continuing with the next source", provider.name)
            statuses.append(provider_status(provider.service, ExternalServiceState.TEMPORARY_FAILURE))
            continue
        statuses.append(result.status)
        if result.evidence is None:
            continue
        fit = fit_cartesian_coordinates(result.evidence)
        if not fit.accepted or fit.coordinates is None:
            reason = f"{provider.name}: {fit.rejection_reason}"
            logger.info("Rejected geometry evidence -- %s", reason)
            rejected.append(reason)
            continue
        return ResolvedGeometry(result.evidence, fit.coordinates, fit, provider.name, tuple(statuses), tuple(rejected))

    ideal = IdealVseprProvider(ideal_shape_target_deg, ideal_shape_source)
    result = ideal.fetch(query)
    statuses.append(result.status)
    if result.evidence is None:
        raise ValueError("No geometry could be resolved, not even an idealized VSEPR model.")
    fit = fit_cartesian_coordinates(result.evidence)
    if not fit.accepted or fit.coordinates is None:
        raise ValueError(f"The idealized VSEPR model failed its own validation: {fit.rejection_reason}")
    return ResolvedGeometry(result.evidence, fit.coordinates, fit, ideal.name, tuple(statuses), tuple(rejected))
