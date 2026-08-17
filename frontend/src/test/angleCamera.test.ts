import { describe, expect, it } from "vitest";
import {
  anglePlaneNormal,
  angleViewQuaternion,
  angleViewSpec,
  applyQuaternion,
  cross,
  dot,
  length,
  rotationBetween,
} from "../components/viewer3d/angleCamera";
import type { BondAngleAnnotation, Structure3D } from "../types/structure3d";
import { chlorineTrifluorideAnalysis, waterAnalysis } from "./fixture";

function annotationOf(structure: Structure3D, label: string): BondAngleAnnotation {
  const found = structure.angle_annotations.find((item) => item.display_label === label);
  if (!found) throw new Error(`no annotation labelled ${label}`);
  return found;
}

/** Angle between the two bond vectors after the camera rotation is applied. */
function projectedAngle(structure: Structure3D, annotation: BondAngleAnnotation): number {
  const quaternion = angleViewQuaternion(structure, annotation)!;
  const atoms = new Map(structure.atoms.map((atom) => [atom.id, atom]));
  const center = atoms.get(annotation.center_atom_id)!;
  const rotate = (id: string) => {
    const atom = atoms.get(id)!;
    return applyQuaternion({ x: atom.x - center.x, y: atom.y - center.y, z: atom.z - center.z }, quaternion);
  };
  // After alignment the plane lies in screen x/y, so the on-screen angle is the 2D one.
  const first = rotate(annotation.atom1_id);
  const second = rotate(annotation.atom2_id);
  const cosine = (first.x * second.x + first.y * second.y) / (Math.hypot(first.x, first.y) * Math.hypot(second.x, second.y));
  return (Math.acos(Math.max(-1, Math.min(1, cosine))) * 180) / Math.PI;
}

describe("angle-view camera alignment", () => {
  it("returns a unit normal perpendicular to both bond vectors", () => {
    const structure = chlorineTrifluorideAnalysis.structure3d;
    const annotation = annotationOf(structure, "87.45°");
    const normal = anglePlaneNormal(structure, annotation)!;
    expect(length(normal)).toBeCloseTo(1, 10);

    const atoms = new Map(structure.atoms.map((atom) => [atom.id, atom]));
    const center = atoms.get(annotation.center_atom_id)!;
    const toAtom = (id: string) => {
      const atom = atoms.get(id)!;
      return { x: atom.x - center.x, y: atom.y - center.y, z: atom.z - center.z };
    };
    expect(dot(normal, toAtom(annotation.atom1_id))).toBeCloseTo(0, 8);
    expect(dot(normal, toAtom(annotation.atom2_id))).toBeCloseTo(0, 8);
  });

  it("rotates the plane normal onto the camera axis", () => {
    const structure = chlorineTrifluorideAnalysis.structure3d;
    const annotation = annotationOf(structure, "87.45°");
    const normal = anglePlaneNormal(structure, annotation)!;
    const rotated = applyQuaternion(normal, angleViewQuaternion(structure, annotation)!);
    expect(rotated.x).toBeCloseTo(0, 8);
    expect(rotated.y).toBeCloseTo(0, 8);
    expect(rotated.z).toBeCloseTo(1, 8);
  });

  it("projects each ClF3 angle at its true value once aligned", () => {
    const structure = chlorineTrifluorideAnalysis.structure3d;
    expect(projectedAngle(structure, annotationOf(structure, "87.45°"))).toBeCloseTo(87.45, 2);
    expect(projectedAngle(structure, annotationOf(structure, "174.90°"))).toBeCloseTo(174.9, 2);
  });

  it("projects the water angle at its true value once aligned", () => {
    const structure = waterAnalysis.structure3d;
    const annotation = structure.angle_annotations[0];
    expect(projectedAngle(structure, annotation)).toBeCloseTo(annotation.value_deg!, 2);
  });

  it("handles a near-linear angle without a degenerate cross product", () => {
    // Two bond vectors 180 deg apart: the cross product vanishes, so the plane is
    // undetermined and any perpendicular direction must be chosen safely.
    const structure: Structure3D = {
      ...waterAnalysis.structure3d,
      atoms: [
        { id: "c", element: "Xe", x: 0, y: 0, z: 0 },
        { id: "a", element: "F", x: 2, y: 0, z: 0 },
        { id: "b", element: "F", x: -2, y: 0, z: 0 },
      ],
    };
    const annotation: BondAngleAnnotation = {
      ...waterAnalysis.structure3d.angle_annotations[0],
      atom1_id: "a", center_atom_id: "c", atom2_id: "b", value_deg: 180,
    };
    const normal = anglePlaneNormal(structure, annotation)!;
    expect(Number.isFinite(normal.x + normal.y + normal.z)).toBe(true);
    expect(length(normal)).toBeCloseTo(1, 10);
    expect(dot(normal, { x: 1, y: 0, z: 0 })).toBeCloseTo(0, 10);
    expect(projectedAngle(structure, annotation)).toBeCloseTo(180, 6);
  });

  it("handles an exactly antiparallel rotation without dividing by zero", () => {
    const quaternion = rotationBetween({ x: 0, y: 0, z: -1 }, { x: 0, y: 0, z: 1 });
    const rotated = applyQuaternion({ x: 0, y: 0, z: -1 }, quaternion);
    expect(rotated.z).toBeCloseTo(1, 8);
    expect(length(cross(quaternion, { x: 0, y: 0, z: 1 }))).toBeGreaterThanOrEqual(0);
  });

  it("preserves translation and zoom when building the view spec", () => {
    const structure = chlorineTrifluorideAnalysis.structure3d;
    const spec = angleViewSpec(structure, annotationOf(structure, "87.45°"), [1, 2, 3, -42, 9, 9, 9, 9])!;
    expect(spec).toHaveLength(8);
    expect(spec.slice(0, 4)).toEqual([1, 2, 3, -42]);
    expect(Math.hypot(spec[4], spec[5], spec[6], spec[7])).toBeCloseTo(1, 8);
  });

  it("returns null when the annotation names atoms that are not present", () => {
    const structure = waterAnalysis.structure3d;
    const annotation = { ...structure.angle_annotations[0], atom1_id: "missing" };
    expect(anglePlaneNormal(structure, annotation)).toBeNull();
    expect(angleViewSpec(structure, annotation, [])).toBeNull();
  });
});
