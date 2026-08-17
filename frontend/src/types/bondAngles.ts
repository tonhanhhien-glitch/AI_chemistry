export type BondAngleEvidenceType = "experimental" | "curated_reference" | "computed_conformer" | "ideal_vsepr";

export interface BondAngleEvidence {
  id: string; atom1_element: string; center_element: string; atom2_element: string;
  atom1_id: string | null; center_atom_id: string | null; atom2_id: string | null;
  value_deg: number | null;
  /** Angle measured from the rendered coordinates, for comparison with `value_deg`. */
  coordinate_value_deg: number | null;
  display_label: string; evidence_type: BondAngleEvidenceType;
  source_name: string; source_url: string | null; reference: string | null; phase: string | null;
  uncertainty_deg: number | null; is_experimental: boolean; is_computed: boolean; is_approximate: boolean;
  equivalent_count: number;
  provenance_label_vi: string | null; provenance_label_en: string | null;
}

export interface BondAnglesResult {
  preferred: BondAngleEvidence[];
  experimental: BondAngleEvidence[];
  coordinate_derived: BondAngleEvidence[];
  curated_reference: BondAngleEvidence[];
  vsepr_prediction: BondAngleEvidence[];
  selection_reason: string;
}
