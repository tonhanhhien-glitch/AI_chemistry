"""Complete VSEPR table for steric numbers two through six in this MVP."""

from dataclasses import asdict, dataclass

from app.core.exceptions import ChemistryValidationError


@dataclass(frozen=True, slots=True)
class VSEPRRule:
    ax_en: str
    bonding_domains: int
    lone_pair_domains: int
    electron_geometry: str
    molecular_geometry: str
    electron_geometry_vi: str
    molecular_geometry_vi: str
    ideal_angle: str
    teaching_note_vi: str


_ROWS = (
    ("AX2", 2, 0, "linear", "linear", "thẳng", "thẳng", "180°",
     "Hai miền electron đẩy nhau về hai phía đối diện."),
    ("AX3", 3, 0, "trigonal planar", "trigonal planar", "tam giác phẳng",
     "tam giác phẳng", "120°", "Ba miền electron nằm trong cùng một mặt phẳng."),
    ("AX2E", 2, 1, "trigonal planar", "bent", "tam giác phẳng", "gấp khúc",
     "<120°", "Một cặp electron tự do nén góc liên kết."),
    ("AX4", 4, 0, "tetrahedral", "tetrahedral", "tứ diện", "tứ diện",
     "109.5°", "Bốn miền liên kết hướng về bốn đỉnh tứ diện."),
    ("AX3E", 3, 1, "tetrahedral", "trigonal pyramidal", "tứ diện",
     "chóp tam giác", "~107°", "Cặp electron tự do chiếm một đỉnh tứ diện và nén góc."),
    ("AX2E2", 2, 2, "tetrahedral", "bent", "tứ diện", "gấp khúc",
     "~104.5°", "Hai cặp electron tự do làm góc liên kết nhỏ hơn góc tứ diện."),
    ("AX5", 5, 0, "trigonal bipyramidal", "trigonal bipyramidal",
     "lưỡng tháp tam giác", "lưỡng tháp tam giác", "90°, 120°, 180°",
     "Có ba vị trí xích đạo và hai vị trí trục."),
    ("AX4E", 4, 1, "trigonal bipyramidal", "seesaw", "lưỡng tháp tam giác",
     "bập bênh", "<90°, <120°, 180°", "Cặp tự do ưu tiên vị trí xích đạo."),
    ("AX3E2", 3, 2, "trigonal bipyramidal", "T-shaped", "lưỡng tháp tam giác",
     "chữ T", "~90°, 180°", "Hai cặp tự do ưu tiên hai vị trí xích đạo."),
    ("AX2E3", 2, 3, "trigonal bipyramidal", "linear", "lưỡng tháp tam giác",
     "thẳng", "180°", "Ba cặp tự do chiếm các vị trí xích đạo."),
    ("AX6", 6, 0, "octahedral", "octahedral", "bát diện", "bát diện",
     "90°, 180°", "Sáu miền liên kết phân bố theo bát diện."),
    ("AX5E", 5, 1, "octahedral", "square pyramidal", "bát diện", "chóp vuông",
     "~90°, 180°", "Một cặp tự do chiếm một đỉnh bát diện."),
    ("AX4E2", 4, 2, "octahedral", "square planar", "bát diện", "vuông phẳng",
     "90°, 180°", "Hai cặp tự do nằm đối diện nhau."),
)

VSEPR_RULES = {row[0]: VSEPRRule(*row) for row in _ROWS}


def ax_notation(bonding_domains: int, lone_pair_domains: int) -> str:
    if lone_pair_domains == 0:
        suffix = ""
    else:
        suffix = "E" if lone_pair_domains == 1 else f"E{lone_pair_domains}"
    return f"AX{bonding_domains}{suffix}"


def get_vsepr_rule(bonding_domains: int, lone_pair_domains: int) -> VSEPRRule:
    notation = ax_notation(bonding_domains, lone_pair_domains)
    try:
        return VSEPR_RULES[notation]
    except KeyError as exc:
        raise ChemistryValidationError(
            f"Phân loại {notation} nằm ngoài phạm vi VSEPR hỗ trợ."
        ) from exc


def vsepr_rule_records() -> list[dict[str, object]]:
    return [asdict(rule) for rule in VSEPR_RULES.values()]
