"""Pedagogical VSEPR-era hybridization labels, not a modern bonding model."""

from app.core.exceptions import ChemistryValidationError

APPROXIMATION_WARNING_VI = (
    "Nhãn lai hoá là mô hình sư phạm gần đúng theo VSEPR, "
    "không phải mô tả liên kết hiện đại đầy đủ."
)
_LABELS = {2: "sp", 3: "sp²", 4: "sp³", 5: "sp³d", 6: "sp³d²"}


def pedagogical_hybridization(steric_number: int) -> tuple[str, str]:
    try:
        return _LABELS[steric_number], APPROXIMATION_WARNING_VI
    except KeyError as exc:
        raise ChemistryValidationError("Số miền electron nằm ngoài phạm vi 2–6.") from exc
