import type { GeometryEvidenceSummary, GeometryEvidenceType } from "./geometryEvidence";

export interface Structure3DAtom {
  id: string;
  element: string;
  x: number;
  y: number;
  z: number;
}

export interface Structure3DBond {
  atom1_id: string;
  atom2_id: string;
  order: number;
}

export interface Vector3D { x: number; y: number; z: number }

export type StructureSource =
  | "experimental_geometry"
  | "curated_coordinates"
  | "pubchem_3d"
  | "rdkit_etkdg"
  | "idealized_vsepr";

/**
 * @deprecated A single number cannot describe a geometry with several inequivalent
 * angles. Use `angle_annotations`, which are measured from the rendered coordinates.
 * No chemistry logic reads this field.
 */
export interface ReferenceBondAngle {
  value_deg: number;
  display_label: string;
  category: "measured" | "curated_reference" | "ideal_vsepr";
  source: string;
  is_approximate: boolean;
  deprecated: boolean;
}

/**
 * One angle of the structure on screen. `coordinate_value_deg` is always measured from
 * the rendered coordinates; `source_value_deg` is the published value when a source
 * observation matched and the coordinates reproduce it. `value_deg` is what to display.
 */
export interface BondAngleAnnotation {
  id: string;
  atom1_id: string;
  center_atom_id: string;
  atom2_id: string;
  value_deg: number | null;
  coordinate_value_deg: number | null;
  source_value_deg: number | null;
  deviation_deg: number | null;
  uncertainty_deg: number | null;
  display_label: string;
  category: "measured" | "conformer" | "ideal_vsepr" | "curated_reference";
  evidence_type: GeometryEvidenceType;
  source: string;
  source_reference: string | null;
  source_url: string | null;
  phase: string | null;
  is_approximate: boolean;
  equivalent_count: number;
  note_vi: string | null;
  note_en: string | null;
}

export interface ElectronDomain3D {
  id: string;
  center_atom_id: string;
  kind: "bonding" | "lone_pair";
  occupancy: number;
  direction: Vector3D;
  position: Vector3D;
  source: string;
  is_illustrative: boolean;
  label_vi: string;
  label_en: string;
}

export interface Structure3D {
  format: "coordinates" | "molblock" | "sdf" | "pdb";
  atoms: Structure3DAtom[];
  bonds: Structure3DBond[];
  data: string | null;
  source: StructureSource;
  source_label: string;
  evidence_type: GeometryEvidenceType;
  geometry_evidence: GeometryEvidenceSummary | null;
  is_illustrative: boolean;
  is_computed: boolean;
  is_experimental: boolean;
  pubchem_cid: number | null;
  central_atom_id: string | null;
  reference_bond_angle: ReferenceBondAngle | null;
  angle_annotations: BondAngleAnnotation[];
  electron_domains: ElectronDomain3D[];
  warning_vi: string | null;
  warning_en: string | null;
}
