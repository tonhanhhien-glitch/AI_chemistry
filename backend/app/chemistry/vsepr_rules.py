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
    teaching_note_en: str


_ROWS = (
    ("AX2", 2, 0, "linear", "linear", "thẳng", "thẳng", "180°",
     "Hai miền electron đẩy nhau về hai phía đối diện.",
     "Two electron domains repel to opposite sides."),
    ("AX3", 3, 0, "trigonal planar", "trigonal planar", "tam giác phẳng",
     "tam giác phẳng", "120°", "Ba miền electron nằm trong cùng một mặt phẳng.",
     "Three electron domains lie in the same plane."),
    ("AX2E", 2, 1, "trigonal planar", "bent", "tam giác phẳng", "gấp khúc",
     "<120°", "Một cặp electron tự do nén góc liên kết.",
     "One lone pair compresses the bond angle."),
    ("AX4", 4, 0, "tetrahedral", "tetrahedral", "tứ diện", "tứ diện",
     "109.5°", "Bốn miền liên kết hướng về bốn đỉnh của một tứ diện.",
     "Four bonding domains point to the four vertices of a tetrahedron."),
    ("AX3E", 3, 1, "tetrahedral", "trigonal pyramidal", "tứ diện",
     "chóp tam giác", "<109.5°",
     "Cặp electron tự do chiếm một đỉnh tứ diện và nén góc liên kết.",
     "The lone pair occupies one tetrahedral vertex and compresses the angle."),
    ("AX2E2", 2, 2, "tetrahedral", "bent", "tứ diện", "gấp khúc",
     "<109.5°", "Hai cặp electron tự do làm góc liên kết nhỏ hơn góc tứ diện.",
     "Two lone pairs make the bond angle smaller than the tetrahedral angle."),
    ("AX5", 5, 0, "trigonal bipyramidal", "trigonal bipyramidal",
     "lưỡng tháp tam giác", "lưỡng tháp tam giác", "90°, 120°, 180°",
     "Có ba vị trí xích đạo và hai vị trí trục.",
     "There are three equatorial and two axial positions."),
    ("AX4E", 4, 1, "trigonal bipyramidal", "seesaw", "lưỡng tháp tam giác",
     "bập bênh", "<90°, <120°, 180°", "Cặp electron tự do ưu tiên vị trí xích đạo.",
     "The lone pair prefers an equatorial position."),
    ("AX3E2", 3, 2, "trigonal bipyramidal", "T-shaped", "lưỡng tháp tam giác",
     "chữ T", "~90°, 180°", "Hai cặp electron tự do ưu tiên hai vị trí xích đạo.",
     "Two lone pairs prefer two equatorial positions."),
    ("AX2E3", 2, 3, "trigonal bipyramidal", "linear", "lưỡng tháp tam giác",
     "thẳng", "180°", "Ba cặp electron tự do chiếm các vị trí xích đạo.",
     "Three lone pairs occupy the equatorial positions."),
    ("AX6", 6, 0, "octahedral", "octahedral", "bát diện", "bát diện",
     "90°, 180°", "Sáu miền liên kết phân bố theo hình bát diện.",
     "Six bonding domains are distributed over an octahedron."),
    ("AX5E", 5, 1, "octahedral", "square pyramidal", "bát diện", "chóp vuông",
     "~90°, 180°", "Một cặp electron tự do chiếm một đỉnh bát diện.",
     "One lone pair occupies one octahedral vertex."),
    ("AX4E2", 4, 2, "octahedral", "square planar", "bát diện", "vuông phẳng",
     "90°, 180°", "Hai cặp electron tự do nằm đối nhau.",
     "Two lone pairs lie opposite each other."),
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
            f"Classification {notation} is outside the supported VSEPR scope."
        ) from exc


def vsepr_rule_records() -> list[dict[str, object]]:
    return [asdict(rule) for rule in VSEPR_RULES.values()]
