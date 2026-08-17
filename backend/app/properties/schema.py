"""Provenance-aware normalized property model.

The old ``PropertyItem`` carried a key, a Vietnamese-only label, a value and a
three-way ``provenance`` string. That cannot express the things a student needs in
order to trust a number: the conditions it was measured at, its uncertainty, the phase
it applies to, whether it applies to this species at all, and where it came from.

Two rules are enforced by construction:

* a property with no value must say *why* -- ``unavailable`` or ``not_applicable`` --
  rather than carry a plausible-looking placeholder;
* a bulk property (melting point, boiling point, density...) is never attached to an
  isolated molecular ion unless the source explicitly describes that exact entity.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class PropertyCategory(StrEnum):
    IDENTITY = "identity"
    STRUCTURAL = "structural"
    PHYSICAL = "physical"
    CHEMICAL = "chemical"


class PropertyEvidenceType(StrEnum):
    EXPERIMENTAL = "experimental"
    SOURCE_ANNOTATION = "source_annotation"
    COMPUTED = "computed"
    CURATED = "curated"
    DETERMINISTIC = "deterministic"


class PropertyApplicability(StrEnum):
    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    UNAVAILABLE = "unavailable"


class PropertyConditions(BaseModel):
    """The state a measurement applies to. An absent field means the source did not say."""

    temperature: str | None = None
    pressure: str | None = None
    solvent: str | None = None
    note: str | None = None

    def is_empty(self) -> bool:
        return not any((self.temperature, self.pressure, self.solvent, self.note))


class PropertyObservation(BaseModel):
    """One individual measurement or quoted observation for a property."""

    value: str | float | int
    unit: str | None = None
    uncertainty: str | float | None = None
    temperature: str | None = None
    pressure: str | None = None
    phase: str | None = None
    method: str | None = None
    evidence_type: PropertyEvidenceType = PropertyEvidenceType.EXPERIMENTAL
    source_name: str
    source_reference: str | None = None
    source_url: str | None = None
    note: str | None = None


class NormalizedProperty(BaseModel):
    key: str
    category: PropertyCategory
    label_vi: str
    label_en: str
    value: str | float | int | None = None
    unit: str | None = None
    uncertainty: str | float | None = None
    conditions: PropertyConditions | None = None
    phase: str | None = None
    evidence_type: PropertyEvidenceType
    source_name: str
    source_reference: str | None = None
    source_url: str | None = None
    applicability: PropertyApplicability = PropertyApplicability.APPLICABLE
    retrieved_at: datetime | None = None
    notes_vi: str | None = None
    notes_en: str | None = None
    observations: list[PropertyObservation] = Field(default_factory=list)

    @model_validator(mode="after")
    def _missing_values_must_be_explained(self) -> "NormalizedProperty":
        if self.value is None and self.applicability is PropertyApplicability.APPLICABLE:
            raise ValueError(
                f"Property '{self.key}' has no value, so it must be marked not_applicable or unavailable."
            )
        if self.value is not None and self.applicability is not PropertyApplicability.APPLICABLE:
            raise ValueError(
                f"Property '{self.key}' carries a value, so it cannot be marked {self.applicability.value}."
            )
        return self


class PropertyProviderStatus(BaseModel):
    provider: str
    service: str
    state: str
    cache_hit: bool = False
    message: str | None = None


class PropertyBundle(BaseModel):
    """Everything known about one species' properties, plus how each lookup went."""

    schema_version: Literal["2.0"] = "2.0"
    formula: str
    charge: int
    properties: list[NormalizedProperty] = Field(default_factory=list)
    statuses: list[PropertyProviderStatus] = Field(default_factory=list)
    partial: bool = False
    """True when at least one provider failed, so the table is known to be incomplete."""

    def by_category(self, category: PropertyCategory) -> list[NormalizedProperty]:
        return [item for item in self.properties if item.category is category]
