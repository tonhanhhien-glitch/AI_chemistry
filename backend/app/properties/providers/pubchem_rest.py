"""PubChem PUG-REST computed properties.

The PUG-REST property service returns PubChem's *computed* descriptors. They are
labelled ``computed`` and attributed to PubChem; none of them is presented as a
measurement.
"""

from __future__ import annotations

import json
import logging

from app.core.config import settings
from app.properties.providers.base import PropertyProviderResult, PropertyQuery
from app.properties.schema import (
    NormalizedProperty,
    PropertyCategory,
    PropertyEvidenceType,
    PropertyProviderStatus,
)
from app.services.pubchem_service import _call_request_bytes, _request_bytes
from app.utils.json_utils import read_json_cache, write_json_cache
import time

logger = logging.getLogger(__name__)

#: PubChem property name -> (key, category, unit, vi label, en label).
_FIELDS: dict[str, tuple[str, PropertyCategory, str | None, str, str]] = {
    "ExactMass": ("exact_mass", PropertyCategory.PHYSICAL, "Da", "Khối lượng chính xác", "Exact mass"),
    "MonoisotopicMass": ("monoisotopic_mass", PropertyCategory.PHYSICAL, "Da", "Khối lượng đơn đồng vị", "Monoisotopic mass"),
    "XLogP": ("xlogp", PropertyCategory.PHYSICAL, None, "XLogP (hệ số phân bố tính toán)", "XLogP (computed partition coefficient)"),
    "TPSA": ("tpsa", PropertyCategory.STRUCTURAL, "Å²", "Diện tích bề mặt phân cực", "Topological polar surface area"),
    "Complexity": ("complexity", PropertyCategory.STRUCTURAL, None, "Độ phức tạp cấu trúc", "Structural complexity"),
    "HBondDonorCount": ("hbond_donor_count", PropertyCategory.CHEMICAL, None, "Số nhóm cho liên kết hydro", "Hydrogen-bond donor count"),
    "HBondAcceptorCount": ("hbond_acceptor_count", PropertyCategory.CHEMICAL, None, "Số nhóm nhận liên kết hydro", "Hydrogen-bond acceptor count"),
    "RotatableBondCount": ("rotatable_bond_count", PropertyCategory.STRUCTURAL, None, "Số liên kết quay tự do", "Rotatable bond count"),
    "IUPACName": ("iupac_name", PropertyCategory.IDENTITY, None, "Tên IUPAC", "IUPAC name"),
    "InChIKey": ("inchikey", PropertyCategory.IDENTITY, None, "InChIKey", "InChIKey"),
}

_REQUEST_FIELDS = ",".join(_FIELDS)


class PubChemRestPropertyProvider:
    """Computed descriptors from the PubChem property service."""

    name = "pubchem_rest"
    service = "PubChem"

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
        key = f"rest:{query.pubchem_cid}"
        now = time.time()
        cached = cache.get(key)
        payload: dict | None = None
        cache_hit = False
        if isinstance(cached, dict) and now - float(cached.get("cached_at", 0)) <= settings.PROPERTY_CACHE_TTL_SECONDS:
            payload = cached.get("payload") if isinstance(cached.get("payload"), dict) else None
            cache_hit = payload is not None
        if payload is None:
            url = (
                f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{query.pubchem_cid}"
                f"/property/{_REQUEST_FIELDS}/JSON"
            )
            try:
                raw, state = _request_bytes(url, timeout=query.timeout)
            except TypeError:
                raw, state = _request_bytes(url)
            if raw is None:
                return PropertyProviderResult((), PropertyProviderStatus(
                    provider=self.name, service=self.service, state=state.value if hasattr(state, "value") else str(state),
                ))
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                return PropertyProviderResult((), PropertyProviderStatus(
                    provider=self.name, service=self.service, state="invalid_response",
                ))
            cache[key] = {"cached_at": now, "payload": payload}
            write_json_cache(cache_path, cache)

        rows = (payload or {}).get("PropertyTable", {}).get("Properties", [])
        if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
            return PropertyProviderResult((), PropertyProviderStatus(
                provider=self.name, service=self.service, state="invalid_response", cache_hit=cache_hit,
            ))

        row = rows[0]
        url = f"https://pubchem.ncbi.nlm.nih.gov/compound/{query.pubchem_cid}"
        properties: list[NormalizedProperty] = [
            NormalizedProperty(
                key="pubchem_cid", category=PropertyCategory.IDENTITY,
                label_vi="PubChem CID", label_en="PubChem CID",
                value=query.pubchem_cid, evidence_type=PropertyEvidenceType.CURATED,
                source_name="PubChem", source_reference=f"PubChem CID {query.pubchem_cid}", source_url=url,
            ),
        ]
        for field, (key_name, category, unit, label_vi, label_en) in _FIELDS.items():
            # Discover what this compound actually has; never assume every field exists.
            if field not in row or row[field] in (None, ""):
                continue
            value = row[field]
            properties.append(NormalizedProperty(
                key=key_name, category=category, label_vi=label_vi, label_en=label_en,
                value=value if isinstance(value, (int, float)) else str(value),
                unit=unit, evidence_type=PropertyEvidenceType.COMPUTED,
                source_name="PubChem", source_reference=f"PubChem CID {query.pubchem_cid}", source_url=url,
                notes_vi="Giá trị do PubChem tính toán, không phải số đo thực nghiệm.",
                notes_en="Value computed by PubChem, not an experimental measurement.",
            ))
        return PropertyProviderResult(
            tuple(properties),
            PropertyProviderStatus(
                provider=self.name, service=self.service,
                state="cache_hit" if cache_hit else "success", cache_hit=cache_hit,
            ),
        )
