/**
 * Camera maths for the "view selected angle" behaviour.
 *
 * When an angle annotation is selected the camera is oriented perpendicular to the
 * plane through atom1–centre–atom2, so the angle projected on screen is the real
 * angle rather than a foreshortened one. Combined with the orthographic projection
 * the viewer uses, what a student measures with a protractor on screen matches the
 * number in the label.
 *
 * These are pure functions on plain vectors, deliberately separate from the 3Dmol
 * component so the geometry can be tested without a WebGL context. No chemistry is
 * calculated here: the atoms, the angle and its value all come from the backend.
 */

import type { BondAngleAnnotation, Structure3D, Vector3D } from "../../types/structure3d";

/** Below this the two bond vectors are collinear and their cross product is noise. */
const NEAR_LINEAR_EPSILON = 1e-6;

export function subtract(left: Vector3D, right: Vector3D): Vector3D {
  return { x: left.x - right.x, y: left.y - right.y, z: left.z - right.z };
}

export function cross(left: Vector3D, right: Vector3D): Vector3D {
  return {
    x: left.y * right.z - left.z * right.y,
    y: left.z * right.x - left.x * right.z,
    z: left.x * right.y - left.y * right.x,
  };
}

export function dot(left: Vector3D, right: Vector3D): number {
  return left.x * right.x + left.y * right.y + left.z * right.z;
}

export function length(vector: Vector3D): number {
  return Math.hypot(vector.x, vector.y, vector.z);
}

export function normalize(vector: Vector3D): Vector3D | null {
  const norm = length(vector);
  if (norm < 1e-12) return null;
  return { x: vector.x / norm, y: vector.y / norm, z: vector.z / norm };
}

/** Any unit vector perpendicular to `vector`; used when a plane is undetermined. */
export function anyPerpendicular(vector: Vector3D): Vector3D {
  const axis: Vector3D = Math.abs(vector.x) < 0.9 ? { x: 1, y: 0, z: 0 } : { x: 0, y: 1, z: 0 };
  return normalize(cross(vector, axis)) ?? { x: 0, y: 0, z: 1 };
}

/**
 * Unit normal of the atom1–centre–atom2 plane.
 *
 * A 180° angle has no unique plane: the cross product vanishes, so any direction
 * perpendicular to the bond axis shows the angle undistorted, and one is chosen
 * deterministically instead of dividing by a near-zero norm.
 */
export function anglePlaneNormal(structure: Structure3D, annotation: BondAngleAnnotation): Vector3D | null {
  const atoms = new Map(structure.atoms.map((atom) => [atom.id, atom]));
  const center = atoms.get(annotation.center_atom_id);
  const first = atoms.get(annotation.atom1_id);
  const second = atoms.get(annotation.atom2_id);
  if (!center || !first || !second) return null;
  const left = normalize(subtract(first, center));
  const right = normalize(subtract(second, center));
  if (!left || !right) return null;
  const product = cross(left, right);
  if (length(product) < NEAR_LINEAR_EPSILON) return anyPerpendicular(left);
  return normalize(product);
}

export interface Quaternion { x: number; y: number; z: number; w: number }

/**
 * Quaternion rotating `from` onto `to`, both assumed unit length.
 *
 * The antiparallel case has no unique shortest arc, so a 180° turn about an
 * arbitrary perpendicular axis is used rather than normalising a zero vector.
 */
export function rotationBetween(from: Vector3D, to: Vector3D): Quaternion {
  const cosine = dot(from, to);
  if (cosine < -1 + 1e-9) {
    const axis = anyPerpendicular(from);
    return { x: axis.x, y: axis.y, z: axis.z, w: 0 };
  }
  const axis = cross(from, to);
  const quaternion = { x: axis.x, y: axis.y, z: axis.z, w: 1 + cosine };
  const norm = Math.hypot(quaternion.x, quaternion.y, quaternion.z, quaternion.w);
  return { x: quaternion.x / norm, y: quaternion.y / norm, z: quaternion.z / norm, w: quaternion.w / norm };
}

/** Apply a unit quaternion to a vector. */
export function applyQuaternion(vector: Vector3D, quaternion: Quaternion): Vector3D {
  const { x, y, z, w } = quaternion;
  const tx = 2 * (y * vector.z - z * vector.y);
  const ty = 2 * (z * vector.x - x * vector.z);
  const tz = 2 * (x * vector.y - y * vector.x);
  return {
    x: vector.x + w * tx + (y * tz - z * ty),
    y: vector.y + w * ty + (z * tx - x * tz),
    z: vector.z + w * tz + (x * ty - y * tx),
  };
}

/**
 * Rotation that brings the angle's plane normal onto the camera axis (+z), i.e. that
 * puts the angle face-on. Returns `null` when the annotation names unknown atoms.
 */
export function angleViewQuaternion(structure: Structure3D, annotation: BondAngleAnnotation): Quaternion | null {
  const normal = anglePlaneNormal(structure, annotation);
  if (!normal) return null;
  return rotationBetween(normal, { x: 0, y: 0, z: 1 });
}

/**
 * 3Dmol `setView` payload: the current translation and zoom with the rotation replaced
 * by the face-on orientation, so aligning the camera never also jumps the zoom level.
 */
export function angleViewSpec(
  structure: Structure3D,
  annotation: BondAngleAnnotation,
  currentView: number[],
): number[] | null {
  const quaternion = angleViewQuaternion(structure, annotation);
  if (!quaternion) return null;
  const [x = 0, y = 0, z = 0, zoom = 0] = currentView;
  return [x, y, z, zoom, quaternion.x, quaternion.y, quaternion.z, quaternion.w];
}
