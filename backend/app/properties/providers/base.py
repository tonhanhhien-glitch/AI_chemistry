"""The property-provider contract, plus the applicability rules every provider obeys."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from app.properties.schema import (
    NormalizedProperty,
    PropertyApplicability,
    PropertyCategory,
    PropertyEvidenceType,
    PropertyProviderStatus,
)

#: Properties of a bulk substance. An isolated molecular ion has no melting point of
#: its own -- what melts is a salt containing it -- so these are refused for charged
#: species unless the source explicitly describes that exact entity.
BULK_PHASE_PROPERTY_KEYS = frozenset({
    "melting_point",
    "boiling_point",
    "density",
    "vapor_pressure",
    "solubility",
    "flash_point",
    "viscosity",
    "refractive_index",
    "heat_of_vaporization",
    "surface_tension",
})


@dataclass(frozen=True, slots=True)
class PropertyQuery:
    """Identity a property provider may look a species up by."""

    formula: str
    charge: int
    atom_inventory: dict[str, int] = field(default_factory=dict)
    pubchem_cid: int | None = None
    inchikey: str | None = None
    cas_rn: str | None = None
    name: str | None = None
    record: dict[str, Any] | None = None
    timeout: float | None = None

    @property
    def is_ion(self) -> bool:
        return self.charge != 0

    def with_timeout(self, timeout: float) -> "PropertyQuery":
        return PropertyQuery(
            formula=self.formula,
            charge=self.charge,
            atom_inventory=self.atom_inventory,
            pubchem_cid=self.pubchem_cid,
            inchikey=self.inchikey,
            cas_rn=self.cas_rn,
            name=self.name,
            record=self.record,
            timeout=timeout,
        )

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "PropertyQuery":
        return cls(
            formula=str(record.get("formula", "")),
            charge=int(record.get("charge", 0)),
            atom_inventory=dict(record.get("atom_inventory") or {}),
            pubchem_cid=record.get("pubchem_cid"),
            inchikey=record.get("inchikey"),
            cas_rn=record.get("cas_rn"),
            name=record.get("name_en") or record.get("name_vi"),
            record=record,
        )


@dataclass(frozen=True, slots=True)
class PropertyProviderResult:
    properties: tuple[NormalizedProperty, ...] = ()
    status: PropertyProviderStatus | None = None


class PropertyProvider(Protocol):
    name: str
    service: str

    def fetch(self, query: PropertyQuery) -> PropertyProviderResult:
        ...


def not_applicable_for_ion(key: str, label_vi: str, label_en: str, source_name: str) -> NormalizedProperty:
    """The honest answer for a bulk property asked of an isolated ion."""

    return NormalizedProperty(
        key=key,
        category=PropertyCategory.PHYSICAL,
        label_vi=label_vi,
        label_en=label_en,
        value=None,
        evidence_type=PropertyEvidenceType.DETERMINISTIC,
        source_name=source_name,
        applicability=PropertyApplicability.NOT_APPLICABLE,
        notes_vi=(
            "Đây là tính chất của chất ở dạng khối. Một ion phân tử cô lập không có giá trị riêng; "
            "giá trị đo được thuộc về muối chứa ion đó, không phải bản thân ion."
        ),
        notes_en=(
            "This is a bulk-substance property. An isolated molecular ion has no value of its own; "
            "a measured value belongs to a salt containing the ion, not to the ion itself."
        ),
    )


def applies_to_entity(key: str, query: PropertyQuery, *, source_describes_exact_entity: bool = False) -> bool:
    """Whether a bulk property may legitimately be attached to this species."""

    if key not in BULK_PHASE_PROPERTY_KEYS:
        return True
    if not query.is_ion:
        return True
    return source_describes_exact_entity
