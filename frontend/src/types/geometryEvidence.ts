/**
 * Mirrors `backend/app/schemas/geometry_evidence_schema.py`. Keep the two in step:
 * a geometry is a collection of observations with an explicit provenance, never a
 * single "the angle" number.
 */

export type GeometryEvidenceType =
  | "experimental"
  | "source_annotation"
  | "computed_conformer"
  | "deterministic_calculation"
  | "ideal_vsepr";

export interface GeometryLengthSummary {
  label: string;
  value_angstrom: number;
  uncertainty_angstrom: number | null;
  equivalent_count: number;
}

export interface GeometryEvidenceSummary {
  id: string;
  evidence_type: GeometryEvidenceType;
  provider: string;
  source_name: string;
  source_reference: string | null;
  source_url: string | null;
  source_comments: string | null;
  retrieved_at: string | null;
  phase: string | null;
  electronic_state: string | null;
  conformation: string | null;
  point_group: string | null;
  units: "angstrom";
  bond_lengths: GeometryLengthSummary[];
  bond_length_count: number;
  bond_angle_count: number;
  dihedral_count: number;
  /** True when the source published internal coordinates and Cartesians were fitted. */
  coordinates_are_fitted: boolean;
  max_length_deviation_angstrom: number | null;
  max_angle_deviation_deg: number | null;
  is_experimental: boolean;
  is_computed: boolean;
  is_ideal: boolean;
  provenance_label_vi: string;
  provenance_label_en: string;
}
