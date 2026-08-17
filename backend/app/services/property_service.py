"""Backwards-compatible entry points over the property-provider architecture.

The normalized model and the providers live in :mod:`app.properties`. This module
keeps the historic import path working and exposes the two call sites the pipeline
uses: the fast, local bundle inlined into ``/analyze`` and the full bundle behind the
lazy ``/properties`` endpoint.
"""

from __future__ import annotations

from typing import Any

from app.properties.providers.base import PropertyQuery
from app.properties.schema import NormalizedProperty, PropertyBundle
from app.properties.service import fast_properties, full_properties

__all__ = ["get_properties", "get_property_bundle", "NormalizedProperty", "PropertyBundle"]


def get_properties(record: dict[str, Any]) -> list[NormalizedProperty]:
    """Local, network-free properties for the inline analysis response."""

    return fast_properties(PropertyQuery.from_record(record)).properties


def get_property_bundle(record: dict[str, Any]) -> PropertyBundle:
    """The complete property table, including external providers."""

    return full_properties(PropertyQuery.from_record(record))
