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
        properties: list[NormalizedProperty] = [
            _identity("formula", "Công thức", "Formula", query.formula),
            _identity("charge", "Điện tích", "Charge", query.charge),
        ]

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
                notes_vi="Tính từ thành phần nguyên tố; không lấy từ mô hình ngôn ngữ.",
                notes_en="Computed from the elemental composition, not taken from a language model.",
            ))

        if record:
            properties.extend([
                _structural("total_valence_electrons", "Tổng electron hoá trị", "Total valence electrons", record["total_valence_electrons"]),
                _structural("ax_en", "Ký hiệu AXnEm", "AXnEm notation", record["ax_en"]),
                _structural("bonding_domains", "Miền liên kết", "Bonding domains", record["bonding_domains"]),
                _structural("lone_pair_domains", "Miền cặp electron tự do", "Lone-pair domains", record["lone_pair_domains"]),
                _structural("steric_number", "Số steric", "Steric number", record["steric_number"]),
                _structural("electron_geometry", "Hình học miền electron", "Electron-domain geometry", record["electron_geometry"]),
                _structural("molecular_geometry", "Hình học phân tử", "Molecular geometry", record["molecular_geometry"]),
                _structural("resonance_forms", "Số công thức cộng hưởng", "Resonance forms", record.get("resonance_forms", 1)),
                _structural(
                    "central_atom_electronegativity", "Độ âm điện nguyên tử trung tâm",
                    "Central-atom electronegativity",
                    get_element(record["central_atom"]).electronegativity or 0.0,
                    unit="Pauling",
                ) if get_element(record["central_atom"]).electronegativity else _unavailable_electronegativity(),
            ])

            polarity = record.get("polarity_note_en") or record.get("polarity_note_vi")
            curated = record.get("source") == "curated"
            if curated and polarity:
                properties.append(NormalizedProperty(
                    key="polarity", category=PropertyCategory.CHEMICAL,
                    label_vi="Nhận xét về độ phân cực", label_en="Polarity note",
                    value=polarity, evidence_type=PropertyEvidenceType.CURATED,
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

            properties.append(_identity(
                "review_status", "Trạng thái rà soát dữ liệu", "Data review status", record["review_status"],
                notes_vi="Chỉ được coi là đã kiểm chứng bên ngoài khi có chữ ký chuyên gia.",
                notes_en="Not labelled externally verified until an expert sign-off exists.",
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
