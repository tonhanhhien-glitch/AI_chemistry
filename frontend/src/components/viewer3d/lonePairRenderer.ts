/**
 * Lone-pair rendering layer for the 3Dmol.js viewer.
 *
 * One non-bonding electron domain is drawn as a single translucent cyan teardrop lobe
 * (a lathed parametric surface added through 3Dmol's custom-shape API) that holds two
 * small opaque red electron spheres. All coordinates are molecular coordinates, so the
 * lobes rotate, zoom and depth-sort together with the molecule.
 *
 * This module is visualization only: directions and domain positions come from the
 * chemistry engine (`Structure3D.electron_domains`) and are never recomputed here.
 */
import type { GLViewer } from "3dmol";
import type { Vector3D } from "../../types/structure3d";

export type LonePairShapeHandle = ReturnType<GLViewer["addSphere"]>;
type LonePairViewer = Pick<GLViewer, "addCustom" | "addSphere" | "removeShape">;

export interface LonePairDomainInput {
  /** Position of the atom the domain belongs to, in molecular coordinates. */
  atomPosition: Vector3D;
  /** Outward VSEPR electron-domain direction (need not be normalized). */
  direction: Vector3D;
  electronCount: number;
  domainType: "lonePair";
  /** Visual radius of the owning atom in the current viewer style, in Angstrom. */
  atomRadius: number;
  /** Distance from the atom to the domain centroid supplied by the chemistry engine. */
  domainDistance: number;
}

/** Axial and radial extents of one lobe, all measured from the atom centre along `direction`. */
export interface LonePairPlacement {
  /** Axial distance where the narrow end of the lobe starts. */
  baseDistance: number;
  /** Axial length of the lobe, narrow end to rounded tip. */
  length: number;
  /** Widest radius of the lobe. */
  maxRadius: number;
  /** Axial distance of the electron pair centre. */
  electronDistance: number;
  /** Sideways offset of each electron from the lobe axis. */
  electronOffset: number;
  electronRadius: number;
}

export interface LocalPairBasis {
  /** Normalized electron-domain direction. */
  axis: Vector3D;
  /** Unit vector perpendicular to `axis`; the two electrons sit at +/- this direction. */
  side: Vector3D;
  /** Third right-handed basis vector, `cross(axis, side)`. */
  up: Vector3D;
}

export interface LobeMesh {
  vertexArr: Vector3D[];
  normalArr: Vector3D[];
  faceArr: number[];
}

export const LONE_PAIR_STYLE = {
  bubbleColor: "#8edff2",
  bubbleOpacity: 0.28,
  electronColor: "#ff1a1a",
  electronOpacity: 1,
  electronQuality: 3,
} as const;

/** Axial samples along the lobe; higher keeps the silhouette smooth rather than polygonal. */
const LOBE_RINGS = 30;
/** Samples around the lobe axis. */
const LOBE_SLICES = 28;
/** Fraction of the lobe length at which the electron pair sits (just past the widest point). */
const ELECTRON_AXIAL_FRACTION = 0.64;
/** Electron offset from the axis and electron radius, both as fractions of `maxRadius`. */
const ELECTRON_OFFSET_FRACTION = 0.42;
const ELECTRON_RADIUS_FRACTION = 0.18;

/** van der Waals radii (Angstrom) for the main-group elements the app renders. */
const VDW_RADII: Record<string, number> = {
  H: 1.2, He: 1.4, Li: 1.82, Be: 1.53, B: 1.92, C: 1.7, N: 1.55, O: 1.52, F: 1.47, Ne: 1.54,
  Na: 2.27, Mg: 1.73, Al: 1.84, Si: 2.1, P: 1.8, S: 1.8, Cl: 1.75, Ar: 1.88,
  K: 2.75, Ca: 2.31, Br: 1.85, Kr: 2.02, I: 1.98, Xe: 2.16, Se: 1.9, Te: 2.06, As: 1.85, Sb: 2.06,
};

function add(left: Vector3D, right: Vector3D): Vector3D { return { x: left.x + right.x, y: left.y + right.y, z: left.z + right.z }; }
function scale(vector: Vector3D, factor: number): Vector3D { return { x: vector.x * factor, y: vector.y * factor, z: vector.z * factor }; }
function cross(left: Vector3D, right: Vector3D): Vector3D {
  return { x: left.y * right.z - left.z * right.y, y: left.z * right.x - left.x * right.z, z: left.x * right.y - left.y * right.x };
}
function normalizeVector(vector: Vector3D): Vector3D {
  const norm = Math.hypot(vector.x, vector.y, vector.z);
  if (norm < 1e-9) throw new Error("Zero-length lone-pair direction");
  return scale(vector, 1 / norm);
}
function clamp(value: number, min: number, max: number): number { return Math.min(max, Math.max(min, value)); }

/** Visual radius of an atom under the current viewer style, used as the base scale for a lobe. */
export function atomVisualRadius(element: string, sphereScale: number): number {
  return (VDW_RADII[element] ?? 1.7) * sphereScale;
}

function rawProfile(t: number): number { return Math.pow(t, 1.15) * Math.sqrt(1 - t * t); }

const LOBE_PROFILE_PEAK = (() => {
  let peak = 0;
  for (let index = 1; index < 1000; index += 1) peak = Math.max(peak, rawProfile(index / 1000));
  return peak;
})();

/**
 * Radius profile of the lobe along its axis, in [0, 1] of `maxRadius`.
 * `t = 0` is the narrow end at the atom, `t = 1` the rounded outer tip: the exponent keeps the
 * neck slender and concave while the square-root factor closes the tip with spherical curvature.
 */
export function lobeProfileRadius(t: number): number {
  if (t <= 0 || t >= 1) return 0;
  return rawProfile(t) / LOBE_PROFILE_PEAK;
}

/**
 * Right-handed basis around the domain direction. The reference vector is swapped whenever it is
 * close to parallel with the direction, so the cross product never degenerates.
 */
export function computeLocalPairBasis(direction: Vector3D): LocalPairBasis {
  const axis = normalizeVector(direction);
  const reference: Vector3D = Math.abs(axis.z) < 0.9 ? { x: 0, y: 0, z: 1 } : { x: 1, y: 0, z: 0 };
  const side = normalizeVector(cross(axis, reference));
  return { axis, side, up: cross(axis, side) };
}

/**
 * Derives the lobe extents from the atom radius and the engine-supplied domain distance:
 * the lobe starts just outside the atom sphere and reaches slightly past the domain centroid.
 */
export function computeLonePairPlacement(atomRadius: number, domainDistance: number): LonePairPlacement {
  const baseDistance = Math.max(atomRadius * 1.06, domainDistance * 0.4);
  const tipDistance = Math.max(domainDistance * 1.3, baseDistance + atomRadius * 1.1);
  const length = tipDistance - baseDistance;
  const maxRadius = clamp(length * 0.4, atomRadius * 0.5, atomRadius * 1.1);
  return {
    baseDistance, length, maxRadius,
    electronDistance: baseDistance + length * ELECTRON_AXIAL_FRACTION,
    electronOffset: maxRadius * ELECTRON_OFFSET_FRACTION,
    electronRadius: maxRadius * ELECTRON_RADIUS_FRACTION,
  };
}

/**
 * Builds the teardrop as a surface of revolution: rings of vertices along the profile plus one
 * apex at each end. Vertex normals come from the analytic meridian slope, so the lobe shades as a
 * smooth volume instead of a faceted solid.
 */
export function createLobeGeometry(atomPosition: Vector3D, basis: LocalPairBasis, placement: LonePairPlacement): LobeMesh {
  const { axis, side, up } = basis;
  const { baseDistance, length, maxRadius } = placement;
  const vertexArr: Vector3D[] = []; const normalArr: Vector3D[] = []; const faceArr: number[] = [];
  const pointAt = (t: number, radius: number, cosine: number, sine: number) =>
    add(atomPosition, add(scale(axis, baseDistance + t * length), add(scale(side, radius * cosine), scale(up, radius * sine))));

  vertexArr.push(add(atomPosition, scale(axis, baseDistance))); normalArr.push(scale(axis, -1));
  for (let ring = 1; ring < LOBE_RINGS; ring += 1) {
    const t = ring / LOBE_RINGS;
    const radius = lobeProfileRadius(t) * maxRadius;
    // Central difference of the profile gives the meridian slope; the outward normal is perpendicular to it.
    const slope = ((lobeProfileRadius(t + 1e-4) - lobeProfileRadius(t - 1e-4)) / 2e-4) * maxRadius;
    for (let slice = 0; slice < LOBE_SLICES; slice += 1) {
      const angle = (2 * Math.PI * slice) / LOBE_SLICES;
      const cosine = Math.cos(angle); const sine = Math.sin(angle);
      const radial = add(scale(side, cosine), scale(up, sine));
      vertexArr.push(pointAt(t, radius, cosine, sine));
      normalArr.push(normalizeVector(add(scale(axis, -slope), scale(radial, length))));
    }
  }
  const tipIndex = vertexArr.length;
  vertexArr.push(add(atomPosition, scale(axis, baseDistance + length))); normalArr.push(axis);

  const ringStart = (ring: number) => 1 + (ring - 1) * LOBE_SLICES;
  for (let slice = 0; slice < LOBE_SLICES; slice += 1) {
    const next = (slice + 1) % LOBE_SLICES;
    faceArr.push(0, ringStart(1) + next, ringStart(1) + slice);
    faceArr.push(ringStart(LOBE_RINGS - 1) + slice, ringStart(LOBE_RINGS - 1) + next, tipIndex);
    for (let ring = 1; ring < LOBE_RINGS - 1; ring += 1) {
      const lower = ringStart(ring); const upper = ringStart(ring + 1);
      faceArr.push(lower + slice, lower + next, upper + next);
      faceArr.push(lower + slice, upper + next, upper + slice);
    }
  }
  return { vertexArr, normalArr, faceArr };
}

/** Centres of the two electrons, offset sideways from the axis so they never overlap each other. */
export function computeElectronCenters(atomPosition: Vector3D, basis: LocalPairBasis, placement: LonePairPlacement): Vector3D[] {
  const center = add(atomPosition, scale(basis.axis, placement.electronDistance));
  return [1, -1].map((sign) => add(center, scale(basis.side, sign * placement.electronOffset)));
}

function createElectronSphere(viewer: LonePairViewer, center: Vector3D, radius: number): LonePairShapeHandle {
  return viewer.addSphere({ center, radius, color: LONE_PAIR_STYLE.electronColor, opacity: LONE_PAIR_STYLE.electronOpacity, quality: LONE_PAIR_STYLE.electronQuality });
}

/** Adds one translucent domain lobe plus its electron spheres and returns the shapes it created. */
export function createLonePairDomain(viewer: LonePairViewer, input: LonePairDomainInput): LonePairShapeHandle[] {
  const basis = computeLocalPairBasis(input.direction);
  const placement = computeLonePairPlacement(input.atomRadius, input.domainDistance);
  const mesh = createLobeGeometry(input.atomPosition, basis, placement);
  // The lobe is added first so the opaque electrons win the depth comparison inside the bubble.
  const shapes = [viewer.addCustom({ ...mesh, color: LONE_PAIR_STYLE.bubbleColor, opacity: LONE_PAIR_STYLE.bubbleOpacity })];
  computeElectronCenters(input.atomPosition, basis, placement)
    .slice(0, Math.max(0, input.electronCount))
    .forEach((center) => shapes.push(createElectronSphere(viewer, center, placement.electronRadius)));
  return shapes;
}

export function renderLonePairDomains(viewer: LonePairViewer, inputs: LonePairDomainInput[]): LonePairShapeHandle[] {
  return inputs.flatMap((input) => createLonePairDomain(viewer, input));
}

export function disposeLonePairObjects(viewer: LonePairViewer, shapes: LonePairShapeHandle[]): void {
  shapes.forEach((shape) => viewer.removeShape(shape));
}

/** Re-creates the lobes in place; 3Dmol shapes are immutable, so moving one means replacing it. */
export function updateLonePairPositions(viewer: LonePairViewer, shapes: LonePairShapeHandle[], inputs: LonePairDomainInput[]): LonePairShapeHandle[] {
  disposeLonePairObjects(viewer, shapes);
  return renderLonePairDomains(viewer, inputs);
}
