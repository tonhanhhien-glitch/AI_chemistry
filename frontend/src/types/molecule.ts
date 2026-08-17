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
  source: "curated" | "cache" | "PubChem reference" | "deterministic";
  confidence: "high" | "medium" | "low";
  pubchem_cid: number | null;
  smiles: string | null;
  canonical_identity: string | null;
  inchi: string | null;
  inchikey: string | null;
  validation_status: string;
  cache_timestamp: string | null;
  connectivity: { atoms: Array<{ id: string; element: string }>; bonds: Array<{ atom1_id: string; atom2_id: string; order: number }>; central_atom_id: string } | null;
}
