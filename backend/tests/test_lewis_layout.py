"""The Lewis layout follows the VSEPR verdict, not the number of bonded atoms."""

import json
import logging
import math
from pathlib import Path

import pytest

from app.chemistry.vsepr_rules import VSEPR_RULES
from app.services.lewis_layout import (
    BARE_ATOM_HALO,
    LONE_PAIR_HALO,
    VIEW_BOX_CENTER,
    VIEW_BOX_HEIGHT,
    VIEW_BOX_MIN_X,
    VIEW_BOX_MIN_Y,
    VIEW_BOX_WIDTH,
    compute_lewis_layout,
    geometry_key,
    get_bond_directions,
    reference_angle_from_record,
)
from app.services.lewis_service import build_lewis_structure
from scripts.export_lewis_layout_fixtures import FIXTURE_PATH, build_fixture_payload

CURATED = json.loads((Path(__file__).resolve().parents[1] / "app" / "data" / "curated_molecules.json").read_text())["molecules"]
BY_FORMULA = {record["formula"]: record for record in CURATED}


def separation(first: float, second: float) -> float:
    """Angle between two directions, in [0, 180]."""

    difference = abs(first - second) % 360
    return 360 - difference if difference > 180 else difference


def bond_angle(record: dict, first: int = 0, second: int = 1) -> float:
    """The drawn angle subtended at the central atom, read back from the coordinates."""

    positions = compute_lewis_layout(record).atom_positions
    center = positions[0]
    vectors = [(positions[i + 1][0] - center[0], positions[i + 1][1] - center[1]) for i in (first, second)]
    return math.degrees(math.acos(
        (vectors[0][0] * vectors[1][0] + vectors[0][1] * vectors[1][1])
        / (math.hypot(*vectors[0]) * math.hypot(*vectors[1]))
    ))


def spec_directions(ax_en: str, **overrides) -> list[float]:
    """Directions for a VSEPR class, addressed by classification rather than by molecule."""

    rule = VSEPR_RULES[ax_en]
    return get_bond_directions(
        overrides.get("molecular_geometry", rule.molecular_geometry),
        rule.bonding_domains, rule.lone_pair_domains, rule.ax_en,
        overrides.get("reference_angle_deg"),
    )


# --- The regression the old atom-count layout could not express ----------------


@pytest.mark.parametrize("ax_en", ["AX2", "AX2E3"])
def test_two_bonded_atoms_stay_linear_when_the_geometry_is_linear(ax_en):
    directions = spec_directions(ax_en)
    assert separation(*directions) == pytest.approx(180)


@pytest.mark.parametrize("ax_en", ["AX2E", "AX2E2"])
def test_two_bonded_atoms_are_drawn_bent_when_the_geometry_is_bent(ax_en):
    directions = spec_directions(ax_en)
    assert separation(*directions) < 160
    # Symmetric about the vertical, i.e. a "V" rather than a tilted pair.
    assert directions[0] + directions[1] == pytest.approx(180)


def test_the_same_bonded_atom_count_yields_different_layouts_per_geometry():
    linear = spec_directions("AX2")
    bent = spec_directions("AX2E2")
    assert len(linear) == len(bent) == 2
    assert separation(*linear) - separation(*bent) > 40


def test_the_lone_pair_count_alone_does_not_decide_the_layout():
    # AX2E3 has more lone pairs than the bent AX2E2 yet is drawn linear.
    assert separation(*spec_directions("AX2E3")) > separation(*spec_directions("AX2E2"))


def test_three_bonded_atoms_differ_between_planar_and_pyramidal():
    planar = sorted(spec_directions("AX3"))
    pyramidal = sorted(spec_directions("AX3E"))
    assert planar != pyramidal
    # The pyramidal fan is compressed into one side, leaving the apex free.
    assert max(separation(a, b) for a in pyramidal for b in pyramidal) < 120


# --- Every supported geometry has a template -----------------------------------


@pytest.mark.parametrize("ax_en", sorted(VSEPR_RULES))
def test_every_vsepr_class_has_a_non_fallback_template(ax_en, caplog):
    rule = VSEPR_RULES[ax_en]
    with caplog.at_level(logging.WARNING):
        directions = spec_directions(ax_en)
    assert len(directions) == rule.bonding_domains
    assert not caplog.records, "a supported geometry must not reach the fallback"
    assert len(set(directions)) == rule.bonding_domains


@pytest.mark.parametrize("ax_en", sorted(VSEPR_RULES))
def test_bonded_atoms_never_overlap_each_other(ax_en):
    directions = spec_directions(ax_en)
    for i, first in enumerate(directions):
        for second in directions[i + 1:]:
            assert separation(first, second) >= 40


def test_geometry_names_from_the_vsepr_table_all_map_to_templates():
    from app.services.lewis_layout import MOLECULAR_GEOMETRY_LAYOUTS

    for rule in VSEPR_RULES.values():
        assert geometry_key(rule.molecular_geometry) in MOLECULAR_GEOMETRY_LAYOUTS


def test_an_unsupported_geometry_falls_back_and_says_so(caplog):
    with caplog.at_level(logging.WARNING):
        directions = get_bond_directions("pentagonal bipyramidal", 7, 0, "AX7")
    assert len(directions) == 7
    assert "no geometric meaning" in caplog.text.lower()


def test_a_template_that_disagrees_with_the_atom_count_falls_back(caplog):
    record = dict(BY_FORMULA["H2O"], atom_symbols=["O", "H", "H", "H"], lone_pairs=[2, 0, 0, 0])
    with caplog.at_level(logging.WARNING):
        layout = compute_lewis_layout(record)
    assert layout.is_fallback
    assert len(layout.terminal_positions) == 3


# --- Reference angles ----------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("~104.5°", 104.5), ("180°", 180.0), ("109.5", 109.5), ("<109.5°", None), ("90°, 120°, 180°", None), (None, None)],
)
def test_only_unambiguous_single_angles_are_read_from_the_record(raw, expected):
    assert reference_angle_from_record({"ideal_angle": raw}) == expected


def test_a_curated_reference_angle_shapes_the_bent_layout():
    assert separation(*spec_directions("AX2E2", reference_angle_deg=97.0)) == pytest.approx(97.0)
    # A value that would make a bent species look straight is refused.
    assert separation(*spec_directions("AX2E2", reference_angle_deg=179.0)) == pytest.approx(104.5)


# --- Whole-structure invariants -------------------------------------------------


@pytest.mark.parametrize("record", CURATED, ids=[record["id"] for record in CURATED])
def test_every_curated_structure_fits_the_view_box(record):
    layout = compute_lewis_layout(record)
    lone_pairs = record["lone_pairs"]
    for (x, y), pairs in zip(layout.atom_positions, lone_pairs, strict=True):
        halo = LONE_PAIR_HALO if pairs > 0 else BARE_ATOM_HALO
        assert VIEW_BOX_MIN_X <= x - halo and x + halo <= VIEW_BOX_MIN_X + VIEW_BOX_WIDTH
        assert VIEW_BOX_MIN_Y <= y - halo and y + halo <= VIEW_BOX_MIN_Y + VIEW_BOX_HEIGHT


@pytest.mark.parametrize("record", CURATED, ids=[record["id"] for record in CURATED])
def test_every_curated_structure_stays_centred_and_deterministic(record):
    layout = compute_lewis_layout(record)
    assert layout.atom_positions == compute_lewis_layout(record).atom_positions
    assert not layout.is_fallback
    # The central atom stays near the middle: only bounding-box centring moves it.
    assert abs(layout.center[0] - VIEW_BOX_CENTER[0]) < 60
    assert abs(layout.center[1] - VIEW_BOX_CENTER[1]) < 60
    xs = [x for x, _ in layout.atom_positions]
    ys = [y for _, y in layout.atom_positions]
    assert (min(xs) + max(xs)) / 2 == pytest.approx(VIEW_BOX_CENTER[0], abs=LONE_PAIR_HALO)
    assert (min(ys) + max(ys)) / 2 == pytest.approx(VIEW_BOX_CENTER[1], abs=LONE_PAIR_HALO)


def test_water_is_drawn_bent_and_carbon_dioxide_stays_linear():
    assert bond_angle(BY_FORMULA["H2O"]) == pytest.approx(104.5, abs=1)
    assert bond_angle(BY_FORMULA["CO2"]) == pytest.approx(180, abs=1)


@pytest.mark.parametrize("formula", ["SO2", "H2O"])
def test_bent_species_are_visibly_not_collinear(formula):
    assert bond_angle(BY_FORMULA[formula]) < 160


def test_water_keeps_its_chemistry_while_changing_its_layout():
    structure = build_lewis_structure(BY_FORMULA["H2O"])
    assert structure.total_valence_electrons == 8
    assert [bond.order for bond in structure.bonds] == [1, 1]
    assert [atom.lone_pairs for atom in structure.atoms] == [2, 0, 0]
    assert all(atom.formal_charge == 0 for atom in structure.atoms)
    hydrogens = [atom for atom in structure.atoms if atom.element == "H"]
    oxygen = structure.atoms[0]
    # Both hydrogens on the same side of O, mirrored about the vertical: a "V".
    assert all(atom.y > oxygen.y for atom in hydrogens)
    assert hydrogens[0].y == pytest.approx(hydrogens[1].y)
    assert (hydrogens[0].x + hydrogens[1].x) / 2 == pytest.approx(oxygen.x)


def test_square_planar_puts_the_four_bonds_on_two_perpendicular_axes():
    layout = compute_lewis_layout(BY_FORMULA["XeF4"])
    directions = sorted(layout.bond_directions)
    assert [separation(directions[i], directions[i + 1]) for i in range(3)] == [90, 90, 90]
    assert separation(directions[0], directions[2]) == pytest.approx(180)


def test_trigonal_planar_keeps_its_three_arms_120_degrees_apart():
    directions = compute_lewis_layout(BY_FORMULA["BF3"]).bond_directions
    for i, first in enumerate(directions):
        for second in directions[i + 1:]:
            assert separation(first, second) == pytest.approx(120)


def test_t_shaped_and_seesaw_leave_the_lone_pair_sites_empty():
    t_shaped = compute_lewis_layout(BY_FORMULA["ClF3"]).bond_directions
    seesaw = compute_lewis_layout(BY_FORMULA["SF4"]).bond_directions
    # Both keep the trigonal-bipyramidal axis; the missing arms are equatorial.
    for directions in (t_shaped, seesaw):
        assert {270.0, 90.0} <= set(directions)
    assert set(seesaw) < set(compute_lewis_layout(BY_FORMULA["PCl5"]).bond_directions)
    assert set(t_shaped) < set(compute_lewis_layout(BY_FORMULA["PCl5"]).bond_directions)


# --- One source of coordinates --------------------------------------------------


def test_the_frontend_layout_fixture_matches_the_backend():
    checked_in = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert checked_in == build_fixture_payload(), (
        "regenerate with: python -m scripts.export_lewis_layout_fixtures"
    )
