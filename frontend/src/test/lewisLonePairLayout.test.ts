import { describe, expect, it } from "vitest";
import type { LewisAtom, LewisBond, LewisStructure } from "../types/lewis";
import {
  ATOM_RADIUS,
  VIEW_BOX,
  angularDistance,
  buildCollisionGeometry,
  distributeAcrossFreeGaps,
  getBondAngles,
  getFreeGaps,
  isConfigurationCollisionFree,
  layoutLonePairs,
  lonePairDots,
  normalizeAngle,
  placeLonePairs,
  scoreConfiguration,
} from "../utils/lewisLonePairLayout";
import layoutFixtures from "./fixtures/lewisLayouts.json";

// The coordinates come from the backend, which is the single source of Lewis layout:
// `backend/scripts/export_lewis_layout_fixtures.py` regenerates this file and a backend
// test fails if it drifts. Deriving the fixtures here instead is what previously let the
// atom-count-only layout live in two places at once.

interface Fixture {
  formula: string;
  ax_en: string;
  electron_geometry: string;
  molecular_geometry: string;
  bonding_domains: number;
  lone_pair_domains: number;
  atoms: LewisAtom[];
  bonds: LewisBond[];
  central_atom_id: string;
}

const molecules: Record<string, Fixture> = Object.fromEntries(
  Object.values(layoutFixtures.molecules).map((molecule) => [
    molecule.formula,
    { ...molecule, bonds: molecule.bonds.map((bond) => ({ ...bond, order: bond.order as 1 | 2 | 3 })) },
  ]),
);

const every = Object.keys(molecules);

function get(formula: string): Fixture {
  const fixture = molecules[formula];
  if (!fixture) throw new Error(`No layout fixture for ${formula}`);
  return fixture;
}

function place(fixture: Fixture, atomId: string): number[] {
  const atom = fixture.atoms.find((candidate) => candidate.id === atomId)!;
  return placeLonePairs(atom, fixture.atoms, fixture.bonds);
}

/** Directions of the bonds leaving the central atom, as drawn. */
function bondDirections(fixture: Fixture): number[] {
  return getBondAngles(fixture.central_atom_id, fixture.atoms, fixture.bonds).map((bond) => bond.angle);
}

/** Every angle subtended at the central atom by a pair of bonds. */
function bondAngles(fixture: Fixture): number[] {
  const directions = bondDirections(fixture);
  return directions.flatMap((first, i) => directions.slice(i + 1).map((second) => angularDistance(first, second)));
}

/** Every electron domain (bonds + lone pairs) around an atom, and the gaps between them. */
function domainGaps(fixture: Fixture, atomId: string): { domains: number[]; gaps: number[] } {
  const bonds = getBondAngles(atomId, fixture.atoms, fixture.bonds).map((bond) => bond.angle);
  const domains = [...place(fixture, atomId), ...bonds].sort((a, b) => a - b);
  return { domains, gaps: domains.map((angle, i) => normalizeAngle(domains[(i + 1) % domains.length] - angle)) };
}

/** Mirror an angle set across the vertical axis of the drawing, as a sorted set. */
function mirrorVertical(angles: number[]): number[] {
  return angles.map((angle) => normalizeAngle(180 - angle)).sort((a, b) => a - b);
}

/** Does every direction have a partner pointing the opposite way? */
function isCentrosymmetric(directions: number[]): boolean {
  return directions.every((angle) => directions.some((other) => angularDistance(angle, other) > 175));
}

describe("geometry-aware bonded-atom layout", () => {
  it("covers every molecular geometry the VSEPR engine can produce", () => {
    expect(new Set(Object.values(molecules).map((fixture) => fixture.molecular_geometry))).toEqual(
      new Set([
        "linear", "bent", "trigonal planar", "trigonal pyramidal", "tetrahedral", "trigonal bipyramidal",
        "seesaw", "T-shaped", "square planar", "square pyramidal", "octahedral",
      ]),
    );
  });

  it.each(every)("draws one bond per bonding domain of %s", (formula) => {
    const fixture = get(formula);
    expect(fixture.bonds).toHaveLength(fixture.bonding_domains);
    expect(fixture.atoms).toHaveLength(fixture.bonding_domains + 1);
    expect(place(fixture, fixture.central_atom_id)).toHaveLength(fixture.lone_pair_domains);
  });

  it.each(every)("keeps every %s atom inside the viewBox", (formula) => {
    for (const atom of get(formula).atoms) {
      expect(atom.x - ATOM_RADIUS).toBeGreaterThanOrEqual(VIEW_BOX.minX);
      expect(atom.x + ATOM_RADIUS).toBeLessThanOrEqual(VIEW_BOX.minX + VIEW_BOX.width);
      expect(atom.y - ATOM_RADIUS).toBeGreaterThanOrEqual(VIEW_BOX.minY);
      expect(atom.y + ATOM_RADIUS).toBeLessThanOrEqual(VIEW_BOX.minY + VIEW_BOX.height);
    }
  });

  it.each(every)("never overlaps two %s atom discs", (formula) => {
    const { atoms } = get(formula);
    for (let i = 0; i < atoms.length; i += 1) {
      for (let j = i + 1; j < atoms.length; j += 1) {
        expect(Math.hypot(atoms[i].x - atoms[j].x, atoms[i].y - atoms[j].y)).toBeGreaterThan(2 * ATOM_RADIUS + 4);
      }
    }
  });

  it.each(every)("keeps the %s drawing centred in the viewBox", (formula) => {
    const { atoms } = get(formula);
    const xs = atoms.map((atom) => atom.x);
    const ys = atoms.map((atom) => atom.y);
    expect(Math.abs((Math.min(...xs) + Math.max(...xs)) / 2 - (VIEW_BOX.minX + VIEW_BOX.width / 2))).toBeLessThan(35);
    expect(Math.abs((Math.min(...ys) + Math.max(...ys)) / 2 - (VIEW_BOX.minY + VIEW_BOX.height / 2))).toBeLessThan(35);
  });

  // The regression that motivated the geometry-aware layout: bonded-atom count alone
  // used to decide the drawing, so every two-bond species came out linear.
  it("draws two bonded atoms differently for linear and for bent species", () => {
    expect(get("CO2").bonding_domains).toBe(get("H2O").bonding_domains);
    expect(bondAngles(get("CO2"))[0]).toBeCloseTo(180, 0);
    expect(bondAngles(get("H2O"))[0]).toBeLessThan(160);
  });

  it.each(["CO2", "XeF2"])("keeps the linear species %s collinear", (formula) => {
    const fixture = get(formula);
    expect(fixture.molecular_geometry).toBe("linear");
    expect(bondAngles(fixture)[0]).toBeCloseTo(180, 0);
    // The two terminal atoms sit opposite each other about the central atom.
    const [center, first, second] = fixture.atoms;
    expect((first.x + second.x) / 2).toBeCloseTo(center.x, 3);
    expect((first.y + second.y) / 2).toBeCloseTo(center.y, 3);
  });

  it.each(["H2O", "SO2"])("bends the bent species %s well away from a straight line", (formula) => {
    const fixture = get(formula);
    expect(fixture.molecular_geometry).toBe("bent");
    const [angle] = bondAngles(fixture);
    expect(angle).toBeLessThan(160);
    expect(angle).toBeGreaterThan(60);
    const [center, first, second] = fixture.atoms;
    // A symmetric "V" with the central atom at the apex, both neighbours below it.
    expect(first.y).toBeGreaterThan(center.y);
    expect(second.y).toBeGreaterThan(center.y);
    expect(first.y).toBeCloseTo(second.y, 3);
    expect((first.x + second.x) / 2).toBeCloseTo(center.x, 3);
  });

  it("draws water at its curated reference angle rather than a generic one", () => {
    expect(bondAngles(get("H2O"))[0]).toBeCloseTo(104.5, 0);
    // AX2E sits on a trigonal-planar skeleton, so it opens wider than AX2E2.
    expect(bondAngles(get("SO2"))[0]).toBeGreaterThan(bondAngles(get("H2O"))[0]);
  });

  it.each(["BF3", "NO3-", "CO3^2-"])("spaces the trigonal-planar %s 120° apart", (formula) => {
    const fixture = get(formula);
    expect(fixture.molecular_geometry).toBe("trigonal planar");
    for (const angle of bondAngles(fixture)) expect(angle).toBeCloseTo(120, 0);
  });

  it("compresses trigonal-pyramidal NH3 into a fan that reads apart from trigonal planar", () => {
    const ammonia = get("NH3");
    expect(ammonia.molecular_geometry).toBe("trigonal pyramidal");
    expect(ammonia.bonds).toHaveLength(3);
    // Every bond within one half of the drawing, leaving the apex to the lone pair.
    expect(Math.max(...bondAngles(ammonia))).toBeLessThan(120);
    expect(Math.max(...bondAngles(ammonia))).toBeGreaterThan(60);
    expect(new Set(bondDirections(ammonia))).not.toEqual(new Set(bondDirections(get("BF3"))));
    const lonePairs = place(ammonia, "a0");
    expect(lonePairs).toHaveLength(1);
    for (const bond of bondDirections(ammonia)) expect(angularDistance(lonePairs[0], bond)).toBeGreaterThan(90);
  });

  it("balances tetrahedral CH4 over four directions rather than one axis", () => {
    const methane = get("CH4");
    expect(methane.bonds).toHaveLength(4);
    expect(isCentrosymmetric(bondDirections(methane))).toBe(true);
    for (const angle of bondAngles(methane)) expect([90, 180]).toContainEqual(Math.round(angle));
    const xs = new Set(methane.atoms.map((atom) => Math.round(atom.x)));
    const ys = new Set(methane.atoms.map((atom) => Math.round(atom.y)));
    expect(xs.size).toBeGreaterThan(1);
    expect(ys.size).toBeGreaterThan(1);
  });

  it("draws square-planar XeF4 as a square with lone pairs on the free diagonals", () => {
    const fixture = get("XeF4");
    expect(fixture.molecular_geometry).toBe("square planar");
    const directions = bondDirections(fixture).sort((a, b) => a - b);
    expect(directions).toHaveLength(4);
    expect(isCentrosymmetric(directions)).toBe(true);
    for (let i = 0; i < 3; i += 1) expect(angularDistance(directions[i], directions[i + 1])).toBeCloseTo(90, 0);
    const lonePairs = place(fixture, "a0");
    expect(lonePairs).toHaveLength(2);
    expect(angularDistance(lonePairs[0], lonePairs[1])).toBeGreaterThan(150);
  });

  it("keeps the trigonal-bipyramidal axis in PCl5, SF4 and ClF3", () => {
    expect(bondDirections(get("SF4"))).toHaveLength(4);
    expect(bondDirections(get("ClF3"))).toHaveLength(3);
    for (const formula of ["PCl5", "SF4", "ClF3"]) {
      const directions = bondDirections(get(formula));
      expect(directions.filter((angle) => directions.some((other) => angularDistance(angle, other) > 175))).toHaveLength(2);
    }
    // Seesaw and T-shape are the bipyramid minus the arms VSEPR gives to lone pairs.
    const bipyramid = new Set(bondDirections(get("PCl5")).map(Math.round));
    for (const formula of ["SF4", "ClF3"]) {
      for (const angle of bondDirections(get(formula))) expect(bipyramid).toContain(Math.round(angle));
    }
  });

  it("puts the seesaw lone pair in the vacant equatorial site", () => {
    const seesaw = get("SF4");
    expect(seesaw.molecular_geometry).toBe("seesaw");
    const [lonePair] = place(seesaw, "a0");
    for (const bond of bondDirections(seesaw)) expect(angularDistance(lonePair, bond)).toBeGreaterThan(40);
    // Opposite the equatorial bonds, which is where the seesaw's open side is.
    expect(angularDistance(lonePair, 180)).toBeLessThan(30);
  });

  it("mirrors the two T-shaped lone pairs about the free axis", () => {
    const tShaped = get("ClF3");
    expect(tShaped.molecular_geometry).toBe("T-shaped");
    const lonePairs = place(tShaped, "a0");
    expect(lonePairs).toHaveLength(2);
    // The free axis of a T points away from its single equatorial bond, so the pairs
    // mirror about the horizontal rather than the vertical.
    const mirrored = lonePairs.map((angle) => normalizeAngle(-angle)).sort((a, b) => a - b);
    expect(mirrored.map(Math.round)).toEqual([...lonePairs].sort((a, b) => a - b).map(Math.round));
  });

  it("gives octahedral SF6 six evenly opposed arms", () => {
    const fixture = get("SF6");
    const directions = bondDirections(fixture).sort((a, b) => a - b);
    expect(directions).toHaveLength(6);
    expect(isCentrosymmetric(directions)).toBe(true);
    for (let i = 0; i < 5; i += 1) expect(angularDistance(directions[i], directions[i + 1])).toBeCloseTo(60, 0);
  });

  it("puts the square-pyramidal lone pair opposite the apex", () => {
    const fixture = get("BrF5");
    expect(fixture.molecular_geometry).toBe("square pyramidal");
    const directions = bondDirections(fixture);
    expect(directions).toHaveLength(5);
    const [lonePair] = place(fixture, "a0");
    const apex = directions.reduce((best, angle) => (angularDistance(angle, lonePair) > angularDistance(best, lonePair) ? angle : best));
    expect(angularDistance(lonePair, apex)).toBeGreaterThan(170);
  });
});

describe("lone-pair placement: no overlap", () => {
  it.each(every)("keeps every %s lone pair out of its bond corridors", (formula) => {
    const fixture = get(formula);
    for (const atom of fixture.atoms) {
      const bonds = getBondAngles(atom.id, fixture.atoms, fixture.bonds);
      for (const angle of place(fixture, atom.id)) {
        for (const bond of bonds) {
          // The narrowest corridor in use is a single bond at ±25°.
          expect(angularDistance(angle, bond.angle)).toBeGreaterThanOrEqual(25);
        }
      }
    }
  });

  it.each(every)("keeps every %s electron dot clear of bonds, atoms and the viewBox edge", (formula) => {
    const fixture = get(formula);
    const geometry = buildCollisionGeometry(fixture.atoms, fixture.bonds);
    for (const atom of fixture.atoms) {
      expect(isConfigurationCollisionFree(atom, place(fixture, atom.id), geometry)).toBe(true);
    }
  });

  it.each(every)("never puts two %s lone pairs on top of each other", (formula) => {
    const fixture = get(formula);
    for (const atom of fixture.atoms) {
      const angles = place(fixture, atom.id);
      for (let i = 0; i < angles.length; i += 1) {
        for (let j = i + 1; j < angles.length; j += 1) expect(angularDistance(angles[i], angles[j])).toBeGreaterThanOrEqual(40);
      }
    }
  });

  // The old renderer spaced lone pairs evenly around the full circle starting at
  // -90°, so a terminal atom bonded straight up or down always got a lone pair
  // drawn directly on top of its bond. Nitrate's double-bonded O showed it worst.
  it("does not repeat the fixed -90°/even-circle placement that sat on the bond", () => {
    expect(place(get("NO3-"), "a1")).not.toContain(90);
    expect(place(get("NO3-"), "a1")).not.toContain(270);
  });
});

describe("lone-pair placement: balance", () => {
  // Bond directions are fixed by the geometry, so perfectly even gaps are not always
  // reachable (NH3's fan stays compressed whatever the lone pair does). What balance
  // does demand is that every lone pair sits mid-way between its two neighbouring
  // domains — that is what makes a crowded side and an empty side impossible.
  it("centres every lone pair between its neighbouring electron domains", () => {
    for (const [formula, fixture] of Object.entries(molecules)) {
      for (const atom of fixture.atoms) {
        if (atom.lone_pairs === 0) continue;
        const chosen = place(fixture, atom.id);
        const { domains, gaps } = domainGaps(fixture, atom.id);
        for (const angle of chosen) {
          const index = domains.indexOf(angle);
          const before = gaps[(index - 1 + gaps.length) % gaps.length];
          const after = gaps[index];
          expect(Math.abs(before - after), `${formula} ${atom.id} lone pair ${angle}° gaps ${before}/${after}`).toBeLessThanOrEqual(20);
        }
      }
    }
  });

  // Water is the acceptance case: two pairs above the bent "V", mirrored, sitting on
  // the free tetrahedral directions rather than smeared over the whole open side.
  it("puts both H2O lone pairs above the oxygen, mirrored about the vertical", () => {
    const water = get("H2O");
    const angles = place(water, "a0");
    expect(angles).toHaveLength(2);
    expect(mirrorVertical(angles)).toEqual(angles);
    for (const angle of angles) {
      // Above the atom in screen space, i.e. on the opposite side to both O–H bonds.
      expect(Math.sin((angle * Math.PI) / 180)).toBeLessThan(0);
      for (const bond of bondDirections(water)) expect(angularDistance(angle, bond)).toBeGreaterThan(70);
    }
    expect(angularDistance(angles[0], angles[1])).toBeGreaterThan(60);
  });

  it("centres the single NH3 lone pair on the molecule's symmetry axis", () => {
    const [angle] = place(get("NH3"), "a0");
    expect(mirrorVertical([angle])).toEqual([angle]);
    // Opposite the downward fan of N–H bonds.
    expect(angle).toBeCloseTo(270, 0);
  });

  it("puts the SO2 central lone pair opposite the two bonds", () => {
    expect(place(get("SO2"), "a0")).toEqual([270]);
  });

  it("balances the nitrate double-bonded O symmetrically about the vertical", () => {
    const angles = place(get("NO3-"), "a1");
    expect(angles).toHaveLength(2);
    expect(mirrorVertical(angles)).toEqual(angles);
    // Upper-left and upper-right, i.e. the free side away from the N=O bond at 90°.
    expect(angles).toEqual([210, 330]);
  });

  it("mirrors the two single-bonded nitrate oxygens", () => {
    expect(mirrorVertical(place(get("NO3-"), "a2"))).toEqual(place(get("NO3-"), "a3"));
    expect(place(get("NO3-"), "a2")).toHaveLength(3);
  });

  it("spreads the three lone pairs of a single-bonded O over its outer side", () => {
    const nitrate = get("NO3-");
    const bond = getBondAngles("a2", nitrate.atoms, nitrate.bonds)[0].angle;
    for (const angle of place(nitrate, "a2")) expect(angularDistance(angle, bond)).toBeGreaterThanOrEqual(85);
  });

  it("mirrors the two CO2 terminal oxygens", () => {
    expect(mirrorVertical(place(get("CO2"), "a1"))).toEqual(place(get("CO2"), "a2"));
  });

  it("keeps the mirrored BF3 fluorines mirrored", () => {
    expect(mirrorVertical(place(get("BF3"), "a2"))).toEqual(place(get("BF3"), "a3"));
  });

  it("prefers the balanced arrangement over an equally collision-free lopsided one", () => {
    const nitrate = get("NO3-");
    const bonds = getBondAngles("a1", nitrate.atoms, nitrate.bonds);
    const context = { bonds, freeAxis: 270 };
    const balanced = scoreConfiguration([210, 330], context);
    expect(balanced).toBeGreaterThan(scoreConfiguration([180, 0], context));
    expect(balanced).toBeGreaterThan(scoreConfiguration([210, 0], context));
    expect(balanced).toBeGreaterThan(scoreConfiguration([180, 225], context));
  });
});

describe("free-sector helpers", () => {
  it("treats the whole circle as free when the atom has no bonds", () => {
    expect(getFreeGaps([])).toEqual([{ start: 0, size: 360 }]);
    expect(distributeAcrossFreeGaps([], 2)).toEqual([90, 270]);
  });

  it("leaves one wrapped free sector opposite a lone terminal bond", () => {
    const gaps = getFreeGaps([{ angle: 90, order: 2 }]);
    expect(gaps).toHaveLength(1);
    expect(gaps[0].size).toBeCloseTo(360 - 64, 5);
    expect(gaps[0].start).toBeCloseTo(122, 5);
  });

  it("splits lone pairs between free sectors in proportion to their width", () => {
    expect(distributeAcrossFreeGaps([{ angle: 0, order: 1 }, { angle: 180, order: 1 }], 2)).toEqual([90, 270]);
  });
});

describe("dot geometry", () => {
  it("lays the two dots out tangentially, centred on the chosen direction", () => {
    const [first, second] = lonePairDots({ x: 100, y: 100 }, 0);
    expect((first.x + second.x) / 2).toBeCloseTo(131, 5);
    expect((first.y + second.y) / 2).toBeCloseTo(100, 5);
    expect(Math.hypot(first.x - second.x, first.y - second.y)).toBeCloseTo(6, 5);
    // Perpendicular to the radius: a pair pointing right is separated vertically.
    expect(first.x).toBeCloseTo(second.x, 5);
  });

  it("keeps the pair perpendicular to the radius at an oblique angle too", () => {
    const angle = 210;
    const [first, second] = lonePairDots({ x: 100, y: 100 }, angle);
    const radial = { x: Math.cos((angle * Math.PI) / 180), y: Math.sin((angle * Math.PI) / 180) };
    const separation = { x: first.x - second.x, y: first.y - second.y };
    expect(radial.x * separation.x + radial.y * separation.y).toBeCloseTo(0, 5);
    expect(Math.hypot(first.x - 100, first.y - 100)).toBeCloseTo(Math.hypot(second.x - 100, second.y - 100), 5);
  });
});

describe("edge cases", () => {
  it("returns nothing for an atom with no lone pairs", () => {
    expect(place(get("CH4"), "a0")).toEqual([]);
  });

  it("spreads the lone pairs of an unbonded atom evenly around the circle", () => {
    const atom: LewisAtom = { id: "a0", element: "Ar", x: 160, y: 140, lone_pairs: 4, formal_charge: 0 };
    const angles = placeLonePairs(atom, [atom], []);
    expect(angles).toHaveLength(4);
    const gaps = angles.map((angle, i) => normalizeAngle(angles[(i + 1) % 4] - angle));
    for (const gap of gaps) expect(gap).toBeCloseTo(90, 5);
  });

  it("still places every lone pair when the atom is crowded with bonds", () => {
    // Seven bonds is past the VSEPR range the layout covers: the backend falls back to
    // an even ring, and the renderer must still find room for every dot.
    const atoms: LewisAtom[] = [
      { id: "a0", element: "Xe", x: 160, y: 140, lone_pairs: 1, formal_charge: 0 },
      ...Array.from({ length: 7 }, (_, i) => ({
        id: `t${i}`, element: "F", lone_pairs: 3, formal_charge: 0,
        x: 160 + 105 * Math.cos((2 * Math.PI * i) / 7 - Math.PI / 2),
        y: 140 + 105 * Math.sin((2 * Math.PI * i) / 7 - Math.PI / 2),
      })),
    ];
    const bonds: LewisBond[] = atoms.slice(1).map((atom, i) => ({ id: `b${i}`, atom1_id: "a0", atom2_id: atom.id, order: 1 as const }));
    for (const atom of atoms) expect(placeLonePairs(atom, atoms, bonds)).toHaveLength(atom.lone_pairs);
  });
});

describe("structure layout", () => {
  it("emits two dots per lone pair for every atom", () => {
    for (const fixture of Object.values(molecules)) {
      const layout = layoutLonePairs(fixture as unknown as Pick<LewisStructure, "atoms" | "bonds">);
      for (const atom of fixture.atoms) {
        expect(layout[atom.id]).toHaveLength(atom.lone_pairs);
        for (const pair of layout[atom.id]) expect(pair.dots).toHaveLength(2);
      }
    }
  });
});
