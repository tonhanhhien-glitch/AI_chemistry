import { describe, expect, it } from "vitest";
import {
  atomVisualRadius, computeElectronCenters, computeLocalPairBasis, computeLonePairPlacement,
  createLobeGeometry, createLonePairDomain, disposeLonePairObjects, lobeProfileRadius,
  type LonePairDomainInput,
} from "../components/viewer3d/lonePairRenderer";
import type { Vector3D } from "../types/structure3d";

const ORIGIN: Vector3D = { x: 0, y: 0, z: 0 };

function distance(left: Vector3D, right: Vector3D): number {
  return Math.hypot(left.x - right.x, left.y - right.y, left.z - right.z);
}

function dot(left: Vector3D, right: Vector3D): number {
  return left.x * right.x + left.y * right.y + left.z * right.z;
}

/** Perpendicular distance from `point` to the axis through `origin` along the unit vector `axis`. */
function radialDistance(point: Vector3D, origin: Vector3D, axis: Vector3D): number {
  const offset = { x: point.x - origin.x, y: point.y - origin.y, z: point.z - origin.z };
  const along = dot(offset, axis);
  return Math.hypot(offset.x - axis.x * along, offset.y - axis.y * along, offset.z - axis.z * along);
}

function viewerStub() {
  const specs: Record<string, unknown>[] = []; const handles: object[] = [];
  const record = (spec: unknown) => { specs.push(spec as Record<string, unknown>); const handle = { spec }; handles.push(handle); return handle as never; };
  return { specs, handles, addCustom: record, addSphere: record, removeShape: (shape: unknown) => { handles.splice(handles.indexOf(shape as object), 1); return undefined as never; } };
}

function domainInput(direction: Vector3D, overrides: Partial<LonePairDomainInput> = {}): LonePairDomainInput {
  return { atomPosition: ORIGIN, direction, electronCount: 2, domainType: "lonePair", atomRadius: atomVisualRadius("O", 0.28), domainDistance: 1.15, ...overrides };
}

describe("lobeProfileRadius", () => {
  it("closes at both ends and peaks in the outer half", () => {
    expect(lobeProfileRadius(0)).toBe(0);
    expect(lobeProfileRadius(1)).toBe(0);
    const samples = Array.from({ length: 199 }, (_, index) => lobeProfileRadius((index + 1) / 200));
    const peak = Math.max(...samples);
    expect(peak).toBeCloseTo(1, 2);
    expect((samples.indexOf(peak) + 1) / 200).toBeGreaterThan(0.5);
  });

  it("is narrower near the atom than at the same distance from the tip", () => {
    expect(lobeProfileRadius(0.2)).toBeLessThan(lobeProfileRadius(0.8));
  });

  it("rounds the tip instead of ending in a point", () => {
    // A spherical cap falls off as sqrt(1 - t): the profile should still be substantial near the tip.
    expect(lobeProfileRadius(0.97)).toBeGreaterThan(0.2);
  });
});

describe("computeLocalPairBasis", () => {
  it.each([
    ["x", { x: 1, y: 0, z: 0 }], ["y", { x: 0, y: 1, z: 0 }], ["z", { x: 0, y: 0, z: 1 }],
    ["diagonal", { x: 0.577, y: 0.577, z: 0.577 }], ["unnormalized", { x: 0, y: 0, z: -4.2 }],
  ] as const)("returns an orthonormal right-handed basis for a %s direction", (_label, direction) => {
    const { axis, side, up } = computeLocalPairBasis(direction);
    [axis, side, up].forEach((vector) => expect(Math.hypot(vector.x, vector.y, vector.z)).toBeCloseTo(1, 6));
    expect(dot(axis, side)).toBeCloseTo(0, 6);
    expect(dot(axis, up)).toBeCloseTo(0, 6);
    expect(dot(side, up)).toBeCloseTo(0, 6);
  });

  it("rejects a zero-length direction rather than emitting a degenerate lobe", () => {
    expect(() => computeLocalPairBasis(ORIGIN)).toThrow(/Zero-length/);
  });
});

describe("computeLonePairPlacement", () => {
  it("starts the lobe outside the atom sphere", () => {
    const placement = computeLonePairPlacement(atomVisualRadius("O", 0.28), 1.15);
    expect(placement.baseDistance).toBeGreaterThan(atomVisualRadius("O", 0.28));
  });

  it("keeps the space-filling lobe clear of the much larger atom sphere", () => {
    const radius = atomVisualRadius("O", 0.95);
    const placement = computeLonePairPlacement(radius, 1.15);
    expect(placement.electronDistance - placement.electronRadius).toBeGreaterThan(radius);
  });

  it("keeps the suggested proportions relative to the atom radius", () => {
    const radius = atomVisualRadius("N", 0.28);
    const placement = computeLonePairPlacement(radius, 1.15);
    expect(placement.maxRadius / radius).toBeGreaterThanOrEqual(0.5);
    expect(placement.maxRadius / radius).toBeLessThanOrEqual(1.1);
    expect(placement.electronRadius / placement.maxRadius).toBeLessThan(0.25);
  });

  it("scales with the molecule instead of using fixed sizes", () => {
    const small = computeLonePairPlacement(0.4, 1.1); const large = computeLonePairPlacement(0.8, 2.2);
    expect(large.length).toBeGreaterThan(small.length);
    expect(large.electronRadius).toBeGreaterThan(small.electronRadius);
  });
});

describe("electron placement", () => {
  const direction = { x: 0.3, y: -0.8, z: 0.52 };
  const basis = computeLocalPairBasis(direction);
  const placement = computeLonePairPlacement(atomVisualRadius("O", 0.28), 1.15);
  const centers = computeElectronCenters(ORIGIN, basis, placement);

  it("produces exactly two electrons that do not overlap each other", () => {
    expect(centers).toHaveLength(2);
    expect(distance(centers[0], centers[1])).toBeGreaterThan(placement.electronRadius * 2);
  });

  it("keeps both electrons clear of the central atom", () => {
    centers.forEach((center) => expect(distance(center, ORIGIN) - placement.electronRadius).toBeGreaterThan(atomVisualRadius("O", 0.28)));
  });

  it("keeps both electrons inside the lobe surface", () => {
    const axialFraction = (dot(centers[0], basis.axis) - placement.baseDistance) / placement.length;
    const lobeRadiusHere = lobeProfileRadius(axialFraction) * placement.maxRadius;
    centers.forEach((center) => expect(radialDistance(center, ORIGIN, basis.axis) + placement.electronRadius).toBeLessThan(lobeRadiusHere));
  });

  it("stays symmetric about the domain axis so rotation keeps the pair balanced", () => {
    expect(dot(centers[0], basis.axis)).toBeCloseTo(dot(centers[1], basis.axis), 9);
    expect(radialDistance(centers[0], ORIGIN, basis.axis)).toBeCloseTo(radialDistance(centers[1], ORIGIN, basis.axis), 9);
  });
});

describe("createLobeGeometry", () => {
  const atom: Vector3D = { x: 1, y: -2, z: 0.5 };
  const basis = computeLocalPairBasis({ x: 0, y: 1, z: 1 });
  const placement = computeLonePairPlacement(atomVisualRadius("N", 0.28), 1.15);
  const mesh = createLobeGeometry(atom, basis, placement);

  it("emits a well-formed indexed mesh", () => {
    expect(mesh.vertexArr.length).toBeGreaterThan(500);
    expect(mesh.normalArr).toHaveLength(mesh.vertexArr.length);
    expect(mesh.faceArr.length % 3).toBe(0);
    expect(Math.max(...mesh.faceArr)).toBe(mesh.vertexArr.length - 1);
    mesh.normalArr.forEach((normal) => expect(Math.hypot(normal.x, normal.y, normal.z)).toBeCloseTo(1, 6));
  });

  it("stays anchored to its atom and never reaches wider than the placement", () => {
    mesh.vertexArr.forEach((vertex) => {
      const along = dot({ x: vertex.x - atom.x, y: vertex.y - atom.y, z: vertex.z - atom.z }, basis.axis);
      expect(along).toBeGreaterThanOrEqual(placement.baseDistance - 1e-9);
      expect(along).toBeLessThanOrEqual(placement.baseDistance + placement.length + 1e-9);
      expect(radialDistance(vertex, atom, basis.axis)).toBeLessThanOrEqual(placement.maxRadius + 1e-9);
    });
  });

  it("tapers toward the atom: the narrow end is thinner than the widest section", () => {
    const radii = mesh.vertexArr.map((vertex) => radialDistance(vertex, atom, basis.axis));
    expect(radii[0]).toBeCloseTo(0, 6);
    expect(radii[radii.length - 1]).toBeCloseTo(0, 6);
    expect(Math.max(...radii)).toBeCloseTo(placement.maxRadius, 2);
  });

  it("rotates with the molecule: the lobe axis follows the domain direction", () => {
    const rotated = createLobeGeometry(atom, computeLocalPairBasis({ x: 1, y: 0, z: 0 }), placement);
    const tip = rotated.vertexArr[rotated.vertexArr.length - 1];
    expect(tip.x - atom.x).toBeCloseTo(placement.baseDistance + placement.length, 6);
    expect(tip.y - atom.y).toBeCloseTo(0, 6);
  });
});

describe("createLonePairDomain", () => {
  it("adds one translucent lobe and two opaque red electrons", () => {
    const viewer = viewerStub();
    const shapes = createLonePairDomain(viewer, domainInput({ x: 0, y: 1, z: 0 }));
    expect(shapes).toHaveLength(3);
    const [lobe, ...electrons] = viewer.specs;
    expect(lobe.color).toBe("#8edff2");
    expect(Number(lobe.opacity)).toBeGreaterThan(0.15); expect(Number(lobe.opacity)).toBeLessThan(0.4);
    expect(electrons).toHaveLength(2);
    electrons.forEach((electron) => { expect(electron.color).toBe("#ff1a1a"); expect(electron.opacity).toBe(1); });
  });

  it("gives every lone pair its own independent bubble", () => {
    const viewer = viewerStub();
    const shapes = [{ x: 0, y: 1, z: 1 }, { x: 0, y: -1, z: 1 }].flatMap((direction) => createLonePairDomain(viewer, domainInput(direction)));
    expect(shapes).toHaveLength(6);
    expect(viewer.specs.filter((spec) => "faceArr" in spec)).toHaveLength(2);
  });

  it("removes every shape it created", () => {
    const viewer = viewerStub();
    disposeLonePairObjects(viewer, createLonePairDomain(viewer, domainInput({ x: 1, y: 0, z: 0 })));
    expect(viewer.handles).toHaveLength(0);
  });
});
