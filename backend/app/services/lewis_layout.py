"""Geometry-aware 2D layout for the Lewis diagram.

The layout is *presentation* geometry derived from the deterministic VSEPR result.
The molecular geometry picks a direction template — disambiguated by the AXnEm label
and the domain counts where one geometry name covers more than one electron-domain
arrangement — and the template is turned into SVG coordinates around the central
atom. Nothing here re-derives chemistry, and nothing here touches the network or an
LLM.

A Lewis diagram is a 2D connectivity/electron picture, not a projection of the real
3D molecule: the templates are the conventional textbook drawings, chosen so that the
picture agrees with the VSEPR classification (a `bent` species must not be drawn
straight) rather than so that it measures like the molecule. `Molecule3DViewer` and
`geometry_templates_3d.json` remain responsible for spatial accuracy.

Angles are degrees in SVG screen space: 0° points right (+x) and 90° points *down*
(+y), so "up" is 270°. This matches frontend/src/utils/lewisLonePairLayout.ts, which
reads these coordinates back out to place the lone-pair dots.
"""

from __future__ import annotations

import logging
import math
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# --- Drawing geometry (must stay in sync with lewisLonePairLayout.ts) ----------

VIEW_BOX_MIN_X = -10.0
VIEW_BOX_MIN_Y = -10.0
VIEW_BOX_WIDTH = 340.0
VIEW_BOX_HEIGHT = 300.0
VIEW_BOX_CENTER = (VIEW_BOX_MIN_X + VIEW_BOX_WIDTH / 2, VIEW_BOX_MIN_Y + VIEW_BOX_HEIGHT / 2)
"""(160, 140) — where the central atom sits when the drawing is already centred."""

BOND_LENGTH = 105.0
MIN_BOND_LENGTH = 45.0
#: Space an atom needs around its centre: the disc plus its stroke, and the lone-pair
#: ring plus a dot when the atom carries lone pairs.
BARE_ATOM_HALO = 22.0
LONE_PAIR_HALO = 34.0

# Screen-space compass points.
RIGHT, DOWN, LEFT, UP = 0.0, 90.0, 180.0, 270.0


def normalize_angle(angle: float) -> float:
    return angle % 360.0


def geometry_key(molecular_geometry: str) -> str:
    """`"T-shaped"` -> `"t_shaped"`, `"trigonal planar"` -> `"trigonal_planar"`."""

    return re.sub(r"[\s-]+", "_", molecular_geometry.strip().lower())


@dataclass(frozen=True, slots=True)
class LayoutSpec:
    """Everything the templates are allowed to look at: no formulas, no atom names."""

    molecular_geometry: str
    bonding_domains: int
    lone_pair_domains: int
    ax_en: str | None = None
    #: Molecule-specific teaching angle from the deterministic record, when it is an
    #: unambiguous single value (e.g. "~104.5°"). Never fetched from a network source.
    reference_angle_deg: float | None = None


# --- Direction templates, one per supported molecular geometry -----------------
#
# Every template returns the directions of the *bonds* only; the lone pairs are
# placed by the renderer's general search in the gaps the bonds leave free, which is
# why several templates deliberately leave a wide gap where VSEPR puts a lone pair.


def _linear(spec: LayoutSpec) -> list[float]:
    """AX2 and AX2E3 alike: two bonds 180° apart. O=C=O, F–Xe–F."""

    return [LEFT, RIGHT]


#: Opening angle of the "V", by lone-pair count: AX2E is a compressed trigonal-planar
#: projection, AX2E2 a compressed tetrahedral one.
_BENT_ANGLE_BY_LONE_PAIRS = {1: 118.0, 2: 104.5}
_BENT_ANGLE_RANGE = (60.0, 160.0)


def _bent_angle(spec: LayoutSpec) -> float:
    reference = spec.reference_angle_deg
    if reference is not None and _BENT_ANGLE_RANGE[0] <= reference <= _BENT_ANGLE_RANGE[1]:
        return reference
    if reference is not None:
        logger.warning("Ignoring out-of-range reference angle %.1f° for a bent layout.", reference)
    return _BENT_ANGLE_BY_LONE_PAIRS.get(spec.lone_pair_domains, 109.5)


def _bent(spec: LayoutSpec) -> list[float]:
    """A "V" opening downwards, so the lone pairs get the free space above the atom."""

    half = _bent_angle(spec) / 2
    return [DOWN + half, DOWN - half]


def _trigonal_planar(spec: LayoutSpec) -> list[float]:
    """Three bonds 120° apart, one pointing up."""

    return [UP, UP + 120.0 - 360.0, UP + 240.0 - 360.0]  # 270, 30, 150


def _trigonal_pyramidal(spec: LayoutSpec) -> list[float]:
    """A downward fan, narrower than trigonal planar, with the apex free for the lone pair.

    The compression is what tells the two three-bond geometries apart on the page; it
    is a drawing convention, not a claim about a projected 3D pyramid.
    """

    return [DOWN + 55.0, DOWN, DOWN - 55.0]  # 145, 90, 35


def _tetrahedral(spec: LayoutSpec) -> list[float]:
    """The conventional Lewis cross, the standard flat drawing of CH4."""

    return [UP, RIGHT, DOWN, LEFT]


#: The trigonal-bipyramidal skeleton, split the way VSEPR fills it: lone pairs take
#: equatorial sites, so seesaw and T-shaped are this template minus equatorial arms.
_AXIAL = (UP, DOWN)
_EQUATORIAL = (LEFT, 40.0, 320.0)


def _trigonal_bipyramidal(spec: LayoutSpec) -> list[float]:
    return [*_AXIAL, *_EQUATORIAL]


def _seesaw(spec: LayoutSpec) -> list[float]:
    """AX4E: the equatorial site the lone pair takes is left empty, pointing left."""

    return [*_AXIAL, *_EQUATORIAL[1:]]


def _t_shaped(spec: LayoutSpec) -> list[float]:
    """AX3E2: both remaining equatorial sites are lone pairs, leaving a literal "T"."""

    return [*_AXIAL, _EQUATORIAL[0]]


def _square_planar(spec: LayoutSpec) -> list[float]:
    """AX4E2: the square, with the two axial lone pairs drawn on the diagonals."""

    return [UP, RIGHT, DOWN, LEFT]


def _square_pyramidal(spec: LayoutSpec) -> list[float]:
    """AX5E: apex up and a four-arm base, leaving the space below the atom free."""

    return [UP, RIGHT, 45.0, 135.0, LEFT]


def _octahedral(spec: LayoutSpec) -> list[float]:
    return [normalize_angle(UP + 60.0 * i) for i in range(6)]


MOLECULAR_GEOMETRY_LAYOUTS: dict[str, Callable[[LayoutSpec], list[float]]] = {
    "linear": _linear,
    "bent": _bent,
    "trigonal_planar": _trigonal_planar,
    "trigonal_pyramidal": _trigonal_pyramidal,
    "tetrahedral": _tetrahedral,
    "trigonal_bipyramidal": _trigonal_bipyramidal,
    "seesaw": _seesaw,
    "t_shaped": _t_shaped,
    "square_planar": _square_planar,
    "square_pyramidal": _square_pyramidal,
    "octahedral": _octahedral,
}


def _fallback_directions(count: int) -> list[float]:
    """Readable but chemically meaningless: an even ring, first arm pointing up."""

    return [normalize_angle(UP + 360.0 * i / count) for i in range(count)]


def _resolve_directions(spec: LayoutSpec, terminal_count: int) -> tuple[list[float], str, bool]:
    """Bond directions, the template that produced them, and whether it is the fallback."""

    key = geometry_key(spec.molecular_geometry)
    if terminal_count <= 0:
        return [], key, False
    if terminal_count == 1:
        return [RIGHT], key, False
    template = MOLECULAR_GEOMETRY_LAYOUTS.get(key)
    if template is None:
        logger.warning(
            "No Lewis layout template for molecular geometry %r (%s); drawing an even "
            "ring of %d bonds, which carries no geometric meaning.",
            spec.molecular_geometry, spec.ax_en or "unknown AXnEm", terminal_count,
        )
        return _fallback_directions(terminal_count), key, True
    directions = [normalize_angle(angle) for angle in template(spec)]
    if len(directions) != terminal_count:
        logger.warning(
            "The %r template draws %d bonds but the structure has %d; falling back to an "
            "even ring, which carries no geometric meaning.",
            key, len(directions), terminal_count,
        )
        return _fallback_directions(terminal_count), key, True
    return directions, key, False


def get_bond_directions(
    molecular_geometry: str,
    bonding_domains: int,
    lone_pair_domains: int,
    ax_en: str | None = None,
    reference_angle_deg: float | None = None,
) -> list[float]:
    """Directions, in SVG degrees, of the bonds leaving the central atom."""

    spec = LayoutSpec(molecular_geometry, bonding_domains, lone_pair_domains, ax_en, reference_angle_deg)
    return _resolve_directions(spec, bonding_domains)[0]


# --- From directions to coordinates -------------------------------------------

_SINGLE_ANGLE = re.compile(r"^[~≈\s]*(\d+(?:\.\d+)?)\s*°?\s*$")


def reference_angle_from_record(record: dict[str, Any]) -> float | None:
    """The record's teaching angle, but only when it states one unambiguous value.

    `"~104.5°"` is a value; `"<109.5°"` is a bound and `"90°, 120°, 180°"` is a set, and
    neither may be read as "draw exactly this".
    """

    raw = record.get("ideal_angle")
    if not isinstance(raw, str):
        return None
    match = _SINGLE_ANGLE.match(raw)
    return float(match.group(1)) if match else None


@dataclass(frozen=True, slots=True)
class LewisLayout:
    """SVG coordinates for one Lewis structure, central atom first."""

    center: tuple[float, float]
    terminal_positions: list[tuple[float, float]]
    bond_directions: list[float]
    bond_length: float
    geometry_key: str
    is_fallback: bool

    @property
    def atom_positions(self) -> list[tuple[float, float]]:
        return [self.center, *self.terminal_positions]

    def bond_angle_deg(self, first: int = 0, second: int = 1) -> float:
        """Angle subtended at the central atom by two bonds, in [0, 180]."""

        difference = abs(self.bond_directions[first] - self.bond_directions[second]) % 360.0
        return 360.0 - difference if difference > 180.0 else difference


def _points(center: tuple[float, float], directions: list[float], radius: float) -> list[tuple[float, float]]:
    return [
        (center[0] + radius * math.cos(math.radians(angle)), center[1] + radius * math.sin(math.radians(angle)))
        for angle in directions
    ]


def _bounds(points: list[tuple[float, float]], halos: list[float]) -> tuple[float, float, float, float]:
    xs_min = [x - halo for (x, _), halo in zip(points, halos, strict=True)]
    xs_max = [x + halo for (x, _), halo in zip(points, halos, strict=True)]
    ys_min = [y - halo for (_, y), halo in zip(points, halos, strict=True)]
    ys_max = [y + halo for (_, y), halo in zip(points, halos, strict=True)]
    return min(xs_min), min(ys_min), max(xs_max), max(ys_max)


def _fits(bounds: tuple[float, float, float, float]) -> bool:
    return bounds[2] - bounds[0] <= VIEW_BOX_WIDTH and bounds[3] - bounds[1] <= VIEW_BOX_HEIGHT


def _fit_bond_length(directions: list[float], halos: list[float]) -> float:
    """The drawing bond length: the default, shrunk only if the diagram would clip."""

    def bounds_at(radius: float) -> tuple[float, float, float, float]:
        return _bounds([VIEW_BOX_CENTER, *_points(VIEW_BOX_CENTER, directions, radius)], halos)

    if _fits(bounds_at(BOND_LENGTH)):
        return BOND_LENGTH
    low, high = 0.0, BOND_LENGTH
    for _ in range(40):
        middle = (low + high) / 2
        if _fits(bounds_at(middle)):
            low = middle
        else:
            high = middle
    logger.warning("Shrinking the Lewis bond length to %.1f so the structure stays inside the viewBox.", low)
    return max(low, MIN_BOND_LENGTH)


def compute_lewis_layout(record: dict[str, Any]) -> LewisLayout:
    """Lay a curated or deterministic record out around a single central atom.

    The record is the source of chemical truth; this only chooses where to draw.
    """

    symbols = record.get("atom_symbols") or []
    terminal_count = max(len(symbols) - 1, 0)
    lone_pairs = list(record.get("lone_pairs") or [])
    spec = LayoutSpec(
        molecular_geometry=str(record.get("molecular_geometry") or ""),
        bonding_domains=int(record.get("bonding_domains") or terminal_count),
        lone_pair_domains=int(record.get("lone_pair_domains") or 0),
        ax_en=record.get("ax_en"),
        reference_angle_deg=reference_angle_from_record(record),
    )
    directions, key, is_fallback = _resolve_directions(spec, terminal_count)
    halos = [
        LONE_PAIR_HALO if index < len(lone_pairs) and lone_pairs[index] > 0 else BARE_ATOM_HALO
        for index in range(terminal_count + 1)
    ]
    radius = _fit_bond_length(directions, halos)
    center = VIEW_BOX_CENTER
    positions = _points(center, directions, radius)
    # Centre the drawing, not the central atom: a downward fan of bonds would otherwise
    # sit low with empty space above it.
    min_x, min_y, max_x, max_y = _bounds([center, *positions], halos)
    shift_x = VIEW_BOX_CENTER[0] - (min_x + max_x) / 2
    shift_y = VIEW_BOX_CENTER[1] - (min_y + max_y) / 2
    center = (round(center[0] + shift_x, 4), round(center[1] + shift_y, 4))
    positions = [(round(x + shift_x, 4), round(y + shift_y, 4)) for x, y in positions]
    return LewisLayout(
        center=center, terminal_positions=positions, bond_directions=directions,
        bond_length=radius, geometry_key=key, is_fallback=is_fallback,
    )
