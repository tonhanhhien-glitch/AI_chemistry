"""PubChem PUG-View annotations: experimental and textual physical/chemical properties.

PUG-View returns a nested tree of annotation *sections*, each with a heading. This
provider walks the tree and keeps the headings it recognises -- it does not assume any
particular molecule has any particular heading, so a species with no measured melting
point simply produces no melting-point row.

Applicability is enforced here: a bulk phase-transition property retrieved for a
charged species is only accepted when the section's own text describes that exact
entity. Otherwise it is reported as ``not_applicable`` with the reason, never as a
value borrowed from the corresponding salt.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from app.core.config import settings
from app.properties.providers.base import (
    BULK_PHASE_PROPERTY_KEYS,
    PropertyProviderResult,
    PropertyQuery,
    not_applicable_for_ion,
)
from app.properties.schema import (
    NormalizedProperty,
    PropertyCategory,
    PropertyEvidenceType,
    PropertyObservation,
    PropertyProviderStatus,
)
from app.services.pubchem_service import _request_bytes
from app.utils.json_utils import read_json_cache, write_json_cache

logger = logging.getLogger(__name__)

#: PubChem heading -> (key, category, vi label, en label). Headings absent from a
#: compound's record are simply not reported.
_HEADINGS: dict[str, tuple[str, PropertyCategory, str, str]] = {
    "Melting Point": ("melting_point", PropertyCategory.PHYSICAL, "Nhiệt độ nóng chảy", "Melting point"),
    "Boiling Point": ("boiling_point", PropertyCategory.PHYSICAL, "Nhiệt độ sôi", "Boiling point"),
    "Density": ("density", PropertyCategory.PHYSICAL, "Khối lượng riêng", "Density"),
    "Vapor Pressure": ("vapor_pressure", PropertyCategory.PHYSICAL, "Áp suất hơi", "Vapor pressure"),
    "Solubility": ("solubility", PropertyCategory.PHYSICAL, "Độ tan", "Solubility"),
    "Flash Point": ("flash_point", PropertyCategory.PHYSICAL, "Điểm chớp cháy", "Flash point"),
    "Viscosity": ("viscosity", PropertyCategory.PHYSICAL, "Độ nhớt", "Viscosity"),
    "Refractive Index": ("refractive_index", PropertyCategory.PHYSICAL, "Chiết suất", "Refractive index"),
    "Physical Description": ("physical_description", PropertyCategory.PHYSICAL, "Mô tả vật lý", "Physical description"),
    "Color/Form": ("color_form", PropertyCategory.PHYSICAL, "Màu sắc / dạng", "Color / form"),
    "Odor": ("odor", PropertyCategory.PHYSICAL, "Mùi", "Odor"),
    "Dissociation Constants": ("dissociation_constants", PropertyCategory.CHEMICAL, "Hằng số phân li", "Dissociation constants"),
    "Decomposition": ("decomposition", PropertyCategory.CHEMICAL, "Sự phân huỷ", "Decomposition"),
    "Heat of Vaporization": ("heat_of_vaporization", PropertyCategory.PHYSICAL, "Nhiệt hoá hơi", "Heat of vaporisation"),
    "Surface Tension": ("surface_tension", PropertyCategory.PHYSICAL, "Sức căng bề mặt", "Surface tension"),
    "Ionization Potential": ("ionization_potential", PropertyCategory.CHEMICAL, "Thế ion hoá", "Ionisation potential"),
}


def _section_text(section: dict[str, Any]) -> tuple[str | None, str | None]:
    """First string value in a section's information block, with its reference."""

    for information in section.get("Information", []) or []:
        if not isinstance(information, dict):
            continue
        value = information.get("Value") or {}
        reference = information.get("Reference")
        if isinstance(reference, list):
            reference = reference[0] if reference else None
        strings = value.get("StringWithMarkup")
        if isinstance(strings, list) and strings and isinstance(strings[0], dict):
            text = strings[0].get("String")
            if isinstance(text, str) and text.strip():
                return text.strip(), reference if isinstance(reference, str) else None
        numbers = value.get("Number")
        if isinstance(numbers, list) and numbers:
            unit = value.get("Unit")
            return f"{numbers[0]}{f' {unit}' if unit else ''}", reference if isinstance(reference, str) else None
    return None, None


def discover_headings(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Walk the PUG-View tree and return every section keyed by its heading.

    Discovery rather than assumption: whatever headings this compound happens to
    publish are what get reported.
    """

    found: dict[str, dict[str, Any]] = {}

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            heading = node.get("TOCHeading")
            if isinstance(heading, str) and heading not in found and node.get("Information"):
                found[heading] = node
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return found


def _section_observations(
    section: dict[str, Any],
    key: str,
    default_evidence_type: PropertyEvidenceType,
    source_url: str,
) -> list[PropertyObservation]:
    """Extract all individual observations from a PUG-View Information block."""

    observations: list[PropertyObservation] = []
    for information in section.get("Information", []) or []:
        if not isinstance(information, dict):
            continue
        value = information.get("Value") or {}
        reference = information.get("Reference")
        if isinstance(reference, list):
            reference = reference[0] if reference else None
        ref_str = str(reference) if reference else None

        text = None
        unit = None
        strings = value.get("StringWithMarkup")
        if isinstance(strings, list) and strings and isinstance(strings[0], dict):
            text_cand = strings[0].get("String")
            if isinstance(text_cand, str) and text_cand.strip():
                text = text_cand.strip()
        if text is None:
            numbers = value.get("Number")
            if isinstance(numbers, list) and numbers:
                unit = value.get("Unit")
                text = f"{numbers[0]}{f' {unit}' if unit else ''}"
        if not text:
            continue

        evidence_type = default_evidence_type
        if key in ("physical_description", "color_form", "odor"):
            evidence_type = PropertyEvidenceType.SOURCE_ANNOTATION

        observations.append(PropertyObservation(
            value=text,
            unit=str(unit) if unit else None,
            evidence_type=evidence_type,
            source_name="PubChem",
            source_reference=ref_str,
            source_url=source_url,
        ))
    return observations


def _describes_exact_entity(text: str, query: PropertyQuery) -> bool:
    """True only when the annotation text names the ion itself rather than a salt.

    PubChem's ion records frequently carry sections inherited from a parent salt. Unless
    the text explicitly says it is about the ion, the value is not attributed to it.
    """

    lowered = text.casefold()
    return "ion" in lowered and query.formula.casefold().rstrip("+-^0123456789") in lowered


class PubChemViewPropertyProvider:
    """Experimental and textual annotations from PubChem's PUG-View service."""

    name = "pubchem_view"
    service = "PubChem View"

    def fetch(self, query: PropertyQuery) -> PropertyProviderResult:
        if not settings.ENABLE_PUBCHEM or not settings.ENABLE_PUBCHEM_PROPERTIES:
            return PropertyProviderResult((), PropertyProviderStatus(provider=self.name, service=self.service, state="disabled"))
        if query.pubchem_cid is None:
            return PropertyProviderResult((), PropertyProviderStatus(
                provider=self.name, service=self.service, state="not_found",
                message="No PubChem CID was resolved for this identity.",
            ))

        cache_path = settings.CACHE_DIR / "pubchem_property_cache.json"
        cache = read_json_cache(cache_path)
        key = f"view:{query.pubchem_cid}"
        now = time.time()
        cached = cache.get(key)
        payload: dict[str, Any] | None = None
        cache_hit = False
        if isinstance(cached, dict) and now - float(cached.get("cached_at", 0)) <= settings.PROPERTY_CACHE_TTL_SECONDS:
            payload = cached.get("payload") if isinstance(cached.get("payload"), dict) else None
            cache_hit = payload is not None
        if payload is None:
            url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{query.pubchem_cid}/JSON"
            raw, state = _request_bytes(url)
            if raw is None:
                return PropertyProviderResult((), PropertyProviderStatus(
                    provider=self.name, service=self.service, state=state.value,
                ))
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return PropertyProviderResult((), PropertyProviderStatus(
                    provider=self.name, service=self.service, state="invalid_response",
                ))
            cache[key] = {"cached_at": now, "payload": payload}
            write_json_cache(cache_path, cache)

        return PropertyProviderResult(
            tuple(self._normalize(payload or {}, query)),
            PropertyProviderStatus(
                provider=self.name, service=self.service,
                state="cache_hit" if cache_hit else "success", cache_hit=cache_hit,
            ),
        )

    def _normalize(self, payload: dict[str, Any], query: PropertyQuery) -> list[NormalizedProperty]:
        sections = discover_headings(payload)
        url = f"https://pubchem.ncbi.nlm.nih.gov/compound/{query.pubchem_cid}"
        properties: list[NormalizedProperty] = []
        for heading, (key, category, label_vi, label_en) in _HEADINGS.items():
            section = sections.get(heading)
            if section is None:
                continue
            default_evidence = (
                PropertyEvidenceType.SOURCE_ANNOTATION
                if key in ("physical_description", "color_form", "odor")
                else PropertyEvidenceType.EXPERIMENTAL
            )
            observations = _section_observations(section, key, default_evidence, url)
            if not observations:
                continue
            first_obs = observations[0]
            if key in BULK_PHASE_PROPERTY_KEYS and query.is_ion and not _describes_exact_entity(str(first_obs.value), query):
                properties.append(not_applicable_for_ion(key, label_vi, label_en, "PubChem"))
                continue
            properties.append(NormalizedProperty(
                key=key, category=category, label_vi=label_vi, label_en=label_en,
                value=first_obs.value,
                unit=first_obs.unit,
                evidence_type=first_obs.evidence_type,
                source_name="PubChem",
                source_reference=first_obs.source_reference,
                source_url=url,
                observations=observations,
                notes_vi="Chú giải lấy nguyên văn từ nguồn PubChem; không do mô hình ngôn ngữ sinh ra.",
                notes_en="Annotation quoted verbatim from the PubChem source; not generated by a language model.",
            ))
        return properties
