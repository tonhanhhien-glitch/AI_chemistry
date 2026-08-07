import { describe, expect, it } from "vitest";
import type { LewisAtom, LewisBond, LewisStructure } from "../types/lewis";
import {
  angularDistance,
  buildCollisionGeometry,
  distributeAcrossFreeGaps,
  getBondAngles,
  getFreeGaps,
  isConfigurationCollisionFree,
  lonePairDots,
  normalizeAngle,
  placeLonePairs,
  scoreConfiguration,
} from "../utils/lewisLonePairLayout";

// Mirrors backend/app/services/lewis_service.py::_positions so the fixtures carry the
// same coordinates the renderer actually receives.
function positions(count: number): [number, number][] {
  if (count === 2) return [[55, 140], [265, 140]];
  const radius = 105;
  return Array.from({ length: count }, (_, i) => {
    const angle = -Math.PI / 2 + (2 * Math.PI * i) / count;
    return [160 + radius * Math.cos(angle), 140 + radius * Math.sin(angle)] as [number, number];
  });
}

function build(symbols: string[], orders: (1 | 2 | 3)[], lonePairs: number[], charges: number[]) {
  const coords: [number, number][] = [[160, 140], ...positions(symbols.length - 1)];
  const atoms: LewisAtom[] = symbols.map((element, i) => ({
    id: `a${i}`,
    element,
    x: coords[i][0],
    y: coords[i][1],
    lone_pairs: lonePairs[i],
    formal_charge: charges[i],
  }));
  const bonds: LewisBond[] = orders.map((order, i) => ({ id: `b${i}`, atom1_id: "a0", atom2_id: `a${i + 1}`, order }));
  return { atoms, bonds };
}

const molecules = {
  H2O: build(["O", "H", "H"], [1, 1], [2, 0, 0], [0, 0, 0]),
  NH3: build(["N", "H", "H", "H"], [1, 1, 1], [1, 0, 0, 0], [0, 0, 0, 0]),
  NH4: build(["N", "H", "H", "H", "H"], [1, 1, 1, 1], [0, 0, 0, 0, 0], [1, 0, 0, 0, 0]),
  CO2: build(["C", "O", "O"], [2, 2], [0, 2, 2], [0, 0, 0]),
  // a1 = top O (double bond), a2 = bottom-right O⁻, a3 = bottom-left O⁻
  NO3: build(["N", "O", "O", "O"], [2, 1, 1], [0, 2, 3, 3], [1, 0, -1, -1]),
  SO2: build(["S", "O", "O"], [2, 1], [1, 2, 3], [1, 0, -1]),
  O3: build(["O", "O", "O"], [2, 1], [1, 2, 3], [1, 0, -1]),
  BF3: build(["B", "F", "F", "F"], [1, 1, 1], [0, 3, 3, 3], [0, 0, 0, 0]),
  CH4: build(["C", "H", "H", "H", "H"], [1, 1, 1, 1], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]),
  HF: build(["F", "H"], [1], [3, 0], [0, 0]),
  XeF4: build(["Xe", "F", "F", "F", "F"], [1, 1, 1, 1], [2, 3, 3, 3, 3], [0, 0, 0, 0, 0]),
} satisfies Record<string, { atoms: LewisAtom[]; bonds: LewisBond[] }>;

type Fixture = (typeof molecules)[keyof typeof molecules];

function place(fixture: Fixture, atomId: string): number[] {
  const atom = fixture.atoms.find((candidate) => candidate.id === atomId)!;
  return placeLonePairs(atom, fixture.atoms, fixture.bonds);
}

/** Every electron domain (bonds + lone pairs) around an atom, and the gaps between them. */
function domainGaps(fixture: Fixture, atomId: string): { domains: number[]; gaps: number[] } {
  const bondAngles = getBondAngles(atomId, fixture.atoms, fixture.bonds).map((bond) => bond.angle);
  const domains = [...place(fixture, atomId), ...bondAngles].sort((a, b) => a - b);
  return { domains, gaps: domains.map((angle, i) => normalizeAngle(domains[(i + 1) % domains.length] - angle)) };
}

/** Mirror an angle set across the vertical axis of the drawing, as a sorted set. */
function mirrorVertical(angles: number[]): number[] {
  return angles.map((angle) => normalizeAngle(180 - angle)).sort((a, b) => a - b);
}

describe("lone-pair placement: no overlap", () => {
  it.each(Object.keys(molecules))("keeps every %s lone pair out of its bond corridors", (name) => {
    const fixture = molecules[name as keyof typeof molecules];
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

  it.each(Object.keys(molecules))("keeps every %s electron dot clear of bonds, atoms and the viewBox edge", (name) => {
    const fixture = molecules[name as keyof typeof molecules];
    const geometry = buildCollisionGeometry(fixture.atoms, fixture.bonds);
    for (const atom of fixture.atoms) {
      expect(isConfigurationCollisionFree(atom, place(fixture, atom.id), geometry)).toBe(true);
    }
  });

  it.each(Object.keys(molecules))("never puts two %s lone pairs on top of each other", (name) => {
    const fixture = molecules[name as keyof typeof molecules];
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
    expect(place(molecules.NO3, "a1")).not.toContain(90);
    expect(place(molecules.NO3, "a1")).not.toContain(270);
    expect(place(molecules.HF, "a0")).not.toContain(270);
  });
});

describe("lone-pair placement: balance", () => {
  // Bond directions are fixed, so perfectly even gaps are not always reachable
  // (NH3's three bonds sit 120° apart whatever the lone pair does). What balance
  // does demand is that every lone pair sits mid-way between its two neighbouring
  // domains — that is what makes a crowded side and an empty side impossible.
  it("centres every lone pair between its neighbouring electron domains", () => {
    for (const [name, fixture] of Object.entries(molecules)) {
      for (const atom of fixture.atoms) {
        if (atom.lone_pairs === 0) continue;
        const chosen = place(fixture, atom.id);
        const { domains, gaps } = domainGaps(fixture, atom.id);
        for (const angle of chosen) {
          const index = domains.indexOf(angle);
          const before = gaps[(index - 1 + gaps.length) % gaps.length];
          const after = gaps[index];
          expect(Math.abs(before - after), `${name} ${atom.id} lone pair ${angle}° gaps ${before}/${after}`).toBeLessThanOrEqual(15);
        }
      }
    }
  });

  it("puts the H2O lone pairs opposite each other, perpendicular to both O–H bonds", () => {
    expect(place(molecules.H2O, "a0")).toEqual([90, 270]);
  });

  it("centres the single NH3 lone pair in a free sector, on the molecule's symmetry axis", () => {
    const [angle] = place(molecules.NH3, "a0");
    const bonds = getBondAngles("a0", molecules.NH3.atoms, molecules.NH3.bonds).map((bond) => bond.angle);
    expect(Math.min(...bonds.map((bond) => angularDistance(angle, bond)))).toBeCloseTo(60, 5);
    // Bonds sit at 270/30/150, so the lone pair at 90 mirrors onto itself.
    expect(angle).toBe(90);
  });

  it("balances the nitrate double-bonded O symmetrically about the vertical", () => {
    const angles = place(molecules.NO3, "a1");
    expect(angles).toHaveLength(2);
    expect(mirrorVertical(angles)).toEqual(angles);
    // Upper-left and upper-right, i.e. the free side away from the N=O bond at 90°.
    expect(angles).toEqual([210, 330]);
  });

  it("mirrors the two single-bonded nitrate oxygens", () => {
    expect(mirrorVertical(place(molecules.NO3, "a2"))).toEqual(place(molecules.NO3, "a3"));
    expect(place(molecules.NO3, "a2")).toHaveLength(3);
  });

  it("spreads the three lone pairs of a single-bonded O over its outer side", () => {
    const bond = getBondAngles("a2", molecules.NO3.atoms, molecules.NO3.bonds)[0].angle;
    for (const angle of place(molecules.NO3, "a2")) expect(angularDistance(angle, bond)).toBeGreaterThanOrEqual(85);
  });

  it("mirrors the two CO2 terminal oxygens", () => {
    expect(mirrorVertical(place(molecules.CO2, "a1"))).toEqual(place(molecules.CO2, "a2"));
  });

  it("puts the SO2 central lone pair opposite the two bonds", () => {
    expect(place(molecules.SO2, "a0")).toEqual([270]);
  });

  it("keeps the mirrored BF3 fluorines mirrored", () => {
    expect(mirrorVertical(place(molecules.BF3, "a2"))).toEqual(place(molecules.BF3, "a3"));
  });

  it("prefers the balanced arrangement over an equally collision-free lopsided one", () => {
    const bonds = getBondAngles("a1", molecules.NO3.atoms, molecules.NO3.bonds);
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
    expect(place(molecules.CH4, "a0")).toEqual([]);
  });

  it("spreads the lone pairs of an unbonded atom evenly around the circle", () => {
    const atom: LewisAtom = { id: "a0", element: "Ar", x: 160, y: 140, lone_pairs: 4, formal_charge: 0 };
    const angles = placeLonePairs(atom, [atom], []);
    expect(angles).toHaveLength(4);
    const gaps = angles.map((angle, i) => normalizeAngle(angles[(i + 1) % 4] - angle));
    for (const gap of gaps) expect(gap).toBeCloseTo(90, 5);
  });

  it("still places every lone pair when the atom is crowded with bonds", () => {
    const structure = build(["Xe", "F", "F", "F", "F", "F", "F"], [1, 1, 1, 1, 1, 1], [1, 3, 3, 3, 3, 3, 3], [0, 0, 0, 0, 0, 0, 0]);
    for (const atom of structure.atoms) {
      expect(placeLonePairs(atom, structure.atoms, structure.bonds)).toHaveLength(atom.lone_pairs);
    }
  });
});

describe("structure layout", () => {
  it("emits two dots per lone pair for every atom", async () => {
    const { layoutLonePairs } = await import("../utils/lewisLonePairLayout");
    const structure = molecules.NO3 as unknown as Pick<LewisStructure, "atoms" | "bonds">;
    const layout = layoutLonePairs(structure);
    for (const atom of structure.atoms) {
      expect(layout[atom.id]).toHaveLength(atom.lone_pairs);
      for (const pair of layout[atom.id]) expect(pair.dots).toHaveLength(2);
    }
  });
});
