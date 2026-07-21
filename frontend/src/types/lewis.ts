export interface LewisAtom {
  id: string;
  element: string;
  x: number;
  y: number;
  lone_pairs: number;
  formal_charge: number;
}

export interface LewisBond {
  id: string;
  atom1_id: string;
  atom2_id: string;
  order: 1 | 2 | 3;
}

export interface LewisStructure {
  atoms: LewisAtom[];
  bonds: LewisBond[];
  central_atom_id: string;
  total_valence_electrons: number;
  resonance_forms: number;
  resonance_note_vi: string | null;
  exception_flags: {
    electron_deficient: boolean;
    expanded_octet: boolean;
    odd_electron: boolean;
    note_vi: string | null;
  };
  source: "curated" | "validated_connectivity";
  confidence: "high" | "medium" | "low";
  review_status: string;
}
