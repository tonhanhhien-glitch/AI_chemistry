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

export interface Structure3D {
  format: "coordinates" | "molblock" | "sdf" | "pdb";
  atoms: Structure3DAtom[];
  bonds: Structure3DBond[];
  data: string | null;
  source: string;
  is_illustrative: boolean;
  warning_vi: string | null;
}
