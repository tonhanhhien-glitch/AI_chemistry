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

export type StructureSource = "curated_coordinates" | "pubchem_3d" | "rdkit_etkdg" | "idealized_vsepr";

/**
 * The molecule-specific angle preferred over the generic AXnEm ideal. `ideal_vsepr` marks the
 * fallback used when the molecule has no specific value of its own.
 */
export interface ReferenceBondAngle {
  value_deg: number;
  display_label: string;
  category: "measured" | "curated_reference" | "ideal_vsepr";
  source: string;
  is_approximate: boolean;
}

export interface BondAngleAnnotation {
  id: string;
  atom1_id: string;
  center_atom_id: string;
  atom2_id: string;
  value_deg: number | null;
  display_label: string;
  category: "measured" | "conformer" | "ideal_vsepr" | "curated_reference";
  source: string;
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
