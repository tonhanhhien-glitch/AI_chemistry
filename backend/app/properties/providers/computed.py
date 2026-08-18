"""Locally computed and curated properties. Always available, never external.

These are the properties ``/analyze`` returns inline, because they are derived from
the deterministic layer that already ran and cost nothing.
"""

from __future__ import annotations

from app.chemistry.periodic_table import get_element
from app.properties.providers.base import PropertyProviderResult, PropertyQuery
from app.properties.schema import (
    NormalizedProperty,
    PropertyApplicability,
    PropertyCategory,
    PropertyEvidenceType,
    PropertyProviderStatus,
)

#: Standard atomic weights (IUPAC conventional values) for the supported elements.
STANDARD_ATOMIC_WEIGHTS = {
    "H": 1.008, "He": 4.0026, "Li": 6.94, "Be": 9.0122, "B": 10.81, "C": 12.011,
    "N": 14.007, "O": 15.999, "F": 18.998, "Ne": 20.180, "Na": 22.990, "Mg": 24.305,
    "Al": 26.982, "Si": 28.085, "P": 30.974, "S": 32.06, "Cl": 35.45, "Ar": 39.95,
    "K": 39.098, "Ca": 40.078, "Br": 79.904, "I": 126.904, "Xe": 131.293,
}

_DETERMINISTIC_SOURCE = "Deterministic chemistry engine"


def molar_mass(atom_inventory: dict[str, int]) -> float | None:
    """Molar mass from standard atomic weights, or ``None`` for an unknown element."""

    total = 0.0
    for symbol, count in atom_inventory.items():
        weight = STANDARD_ATOMIC_WEIGHTS.get(symbol)
        if weight is None:
            return None
        total += weight * count
    return round(total, 3)


def _identity(key: str, label_vi: str, label_en: str, value: str | float | int, **extra: object) -> NormalizedProperty:
    return NormalizedProperty(
        key=key, category=PropertyCategory.IDENTITY, label_vi=label_vi, label_en=label_en,
        value=value, evidence_type=PropertyEvidenceType.DETERMINISTIC,
        source_name=_DETERMINISTIC_SOURCE, **extra,
    )


def _structural(key: str, label_vi: str, label_en: str, value: str | float | int, **extra: object) -> NormalizedProperty:
    return NormalizedProperty(
        key=key, category=PropertyCategory.STRUCTURAL, label_vi=label_vi, label_en=label_en,
        value=value, evidence_type=PropertyEvidenceType.DETERMINISTIC,
        source_name=_DETERMINISTIC_SOURCE, **extra,
    )


class ComputedPropertyProvider:
    """Properties this application derives itself from the resolved record."""

    name = "computed"
    service = "Deterministic chemistry"

    def fetch(self, query: PropertyQuery) -> PropertyProviderResult:
        record = query.record or {}
        properties: list[NormalizedProperty] = []

        mass = molar_mass(query.atom_inventory)
        if mass is None:
            properties.append(NormalizedProperty(
                key="molar_mass", category=PropertyCategory.PHYSICAL,
                label_vi="Khối lượng mol", label_en="Molar mass", value=None,
                evidence_type=PropertyEvidenceType.COMPUTED, source_name=_DETERMINISTIC_SOURCE,
                applicability=PropertyApplicability.UNAVAILABLE,
                notes_vi="Thiếu khối lượng nguyên tử chuẩn cho ít nhất một nguyên tố.",
                notes_en="A standard atomic weight is missing for at least one element.",
            ))
        else:
            properties.append(NormalizedProperty(
                key="molar_mass", category=PropertyCategory.PHYSICAL,
                label_vi="Khối lượng mol", label_en="Molar mass",
                value=mass, unit="g/mol", evidence_type=PropertyEvidenceType.COMPUTED,
                source_name="Standard atomic weights (IUPAC)",
                source_name_en="Standard atomic weights (IUPAC)",
                source_name_vi="Khối lượng nguyên tử chuẩn (IUPAC)",
            ))

        if record:
            central = record.get("central_atom")
            if central:
                elem_info = get_element(central)
                if elem_info.electronegativity:
                    properties.append(_structural(
                        "central_atom_electronegativity", "Độ âm điện nguyên tử trung tâm",
                        "Central-atom electronegativity",
                        elem_info.electronegativity,
                        unit="Pauling",
                    ))
                else:
                    properties.append(_unavailable_electronegativity())

            polarity_en = record.get("polarity_note_en")
            polarity_vi = record.get("polarity_note_vi")
            curated = record.get("source") == "curated"
            if curated and (polarity_en or polarity_vi):
                properties.append(NormalizedProperty(
                    key="polarity", category=PropertyCategory.CHEMICAL,
                    label_vi="Nhận xét về độ phân cực", label_en="Polarity note",
                    value=polarity_en or polarity_vi,
                    value_en=polarity_en,
                    value_vi=polarity_vi,
                    evidence_type=PropertyEvidenceType.CURATED,
                    source_name="Curated teaching record",
                ))
            else:
                properties.append(NormalizedProperty(
                    key="polarity", category=PropertyCategory.CHEMICAL,
                    label_vi="Nhận xét về độ phân cực", label_en="Polarity note", value=None,
                    evidence_type=PropertyEvidenceType.DETERMINISTIC, source_name=_DETERMINISTIC_SOURCE,
                    applicability=PropertyApplicability.UNAVAILABLE,
                    notes_vi="Không suy luận độ phân cực cho bản ghi chưa được tuyển chọn.",
                    notes_en="Polarity is not inferred for an uncurated record.",
                ))

        return PropertyProviderResult(
            tuple(properties),
            PropertyProviderStatus(provider=self.name, service=self.service, state="success"),
        )


def _unavailable_electronegativity() -> NormalizedProperty:
    return NormalizedProperty(
        key="central_atom_electronegativity", category=PropertyCategory.STRUCTURAL,
        label_vi="Độ âm điện nguyên tử trung tâm", label_en="Central-atom electronegativity",
        value=None, evidence_type=PropertyEvidenceType.DETERMINISTIC, source_name=_DETERMINISTIC_SOURCE,
        applicability=PropertyApplicability.UNAVAILABLE,
        notes_vi="Không có giá trị độ âm điện Pauling cho nguyên tố này.",
        notes_en="No Pauling electronegativity is defined for this element.",
    )
