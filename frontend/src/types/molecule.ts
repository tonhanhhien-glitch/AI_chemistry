export interface MoleculeSummary {
  id: string;
  formula: string;
  name_vi: string;
  name_en: string;
  ax_en: string;
  molecular_geometry: string;
  molecular_geometry_vi: string;
  review_status: string;
}

export interface Molecule extends MoleculeSummary {
  charge: number;
  atom_inventory: Record<string, number>;
  central_atom: string;
  source: "curated" | "cache" | "PubChem reference";
  confidence: "high" | "medium" | "low";
  pubchem_cid: number | null;
  smiles: string | null;
}

export interface PropertyItem {
  key: string;
  label_vi: string;
  value: string | number;
  unit: string | null;
  provenance: "curated" | "computed" | "PubChem reference";
  verified_teaching_fact: boolean;
  note_vi: string | null;
}
