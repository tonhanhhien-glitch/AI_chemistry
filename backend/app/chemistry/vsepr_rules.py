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


# Backend content is English. The `*_vi` fields mirror the English geometry
# names and teaching notes here; the frontend localizes them via its i18n layer
# (see frontend geometry labels + rules.teachingNote.* keyed by AXnEm).
_ROWS = (
    ("AX2", 2, 0, "linear", "linear", "linear", "linear", "180°",
     "Two electron domains repel to opposite sides."),
    ("AX3", 3, 0, "trigonal planar", "trigonal planar", "trigonal planar",
     "trigonal planar", "120°", "Three electron domains lie in the same plane."),
    ("AX2E", 2, 1, "trigonal planar", "bent", "trigonal planar", "bent",
     "<120°", "One lone pair compresses the bond angle."),
    ("AX4", 4, 0, "tetrahedral", "tetrahedral", "tetrahedral", "tetrahedral",
     "109.5°", "Four bonding domains point to the four vertices of a tetrahedron."),
    ("AX3E", 3, 1, "tetrahedral", "trigonal pyramidal", "tetrahedral",
     "trigonal pyramidal", "~107°", "The lone pair occupies one tetrahedral vertex and compresses the angle."),
    ("AX2E2", 2, 2, "tetrahedral", "bent", "tetrahedral", "bent",
     "~104.5°", "Two lone pairs make the bond angle smaller than the tetrahedral angle."),
    ("AX5", 5, 0, "trigonal bipyramidal", "trigonal bipyramidal",
     "trigonal bipyramidal", "trigonal bipyramidal", "90°, 120°, 180°",
     "There are three equatorial and two axial positions."),
    ("AX4E", 4, 1, "trigonal bipyramidal", "seesaw", "trigonal bipyramidal",
     "seesaw", "<90°, <120°, 180°", "The lone pair prefers an equatorial position."),
    ("AX3E2", 3, 2, "trigonal bipyramidal", "T-shaped", "trigonal bipyramidal",
     "T-shaped", "~90°, 180°", "Two lone pairs prefer two equatorial positions."),
    ("AX2E3", 2, 3, "trigonal bipyramidal", "linear", "trigonal bipyramidal",
     "linear", "180°", "Three lone pairs occupy the equatorial positions."),
    ("AX6", 6, 0, "octahedral", "octahedral", "octahedral", "octahedral",
     "90°, 180°", "Six bonding domains are distributed over an octahedron."),
    ("AX5E", 5, 1, "octahedral", "square pyramidal", "octahedral", "square pyramidal",
     "~90°, 180°", "One lone pair occupies one octahedral vertex."),
    ("AX4E2", 4, 2, "octahedral", "square planar", "octahedral", "square planar",
     "90°, 180°", "Two lone pairs lie opposite each other."),
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
