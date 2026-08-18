/** Mirrors `backend/app/schemas/molecule_admin.py`. */

import type { NormalizedProperty } from "./properties";

export interface AdminSessionStatus {
  authenticated: boolean;
  username: string | null;
}

export interface ExceptionFlags {
  electron_deficient: boolean;
  expanded_octet: boolean;
  odd_electron: boolean;
}

export interface ThreeDSource {
  kind: string;
  verified_reference: boolean;
}

export interface ResonanceStructureDraft {
  form_index: number;
  bond_orders: number[];
  lone_pairs: number[];
  formal_charges: number[];
}

export interface ReviewProvenance {
  source_name: string | null;
  reference: string | null;
  url: string | null;
  evidence_type: string | null;
  conditions: string | null;
  retrieved_at: string | null;
}

/** A molecule record, editable through the admin page. Extra fields the frontend
 * does not know about round-trip unchanged (the backend model allows them). */
export interface MoleculeDraft {
  id: string;
  formula: string;
  charge: number;
  name_vi: string;
  name_en: string;
  aliases: string[];

  cas_rn: string | null;
  pubchem_cid: number | null;
  smiles: string | null;
  inchi: string | null;
  inchikey: string | null;

  atom_inventory: Record<string, number>;
  atom_symbols: string[];
  central_atom: string;

  total_valence_electrons: number;
  bond_orders: number[];
  lone_pairs: number[];
  formal_charges: number[];
  resonance_forms: number;
  resonance_structures: ResonanceStructureDraft[];
  resonance_note_vi: string | null;
  resonance_note_en: string | null;
  exception_flags: ExceptionFlags;

  bonding_domains: number;
  lone_pair_domains: number;
  steric_number: number;
  ax_en: string;
  electron_geometry: string;
  electron_geometry_vi: string;
  molecular_geometry: string;
  molecular_geometry_vi: string;
  ideal_angle: string;
  distortion_note_vi: string | null;
  distortion_note_en: string | null;
  hybridization: string | null;
  hybridization_warning_vi: string | null;
  hybridization_warning_en: string | null;
  polarity_note_vi: string | null;
  polarity_note_en: string | null;

  teaching_note_vi: string | null;
  teaching_note_en: string | null;
  misconception_note_vi: string | null;
  misconception_note_en: string | null;
  structure_property_note_vi: string | null;
  structure_property_note_en: string | null;

  three_d_source: ThreeDSource;
  source: "curated" | "cache" | "PubChem reference" | "deterministic";
  confidence: "high" | "medium" | "low";
  review_status: string;
  review_provenance: ReviewProvenance | null;
}

export interface GeometryAtomDraft { id: string; element: string; role: "center" | "ligand" | "other" }
export interface GeometryBondDraft { atom1_id: string; atom2_id: string; order: number }
export interface GeometryCoordinateDraft { id: string; element: string; x: number; y: number; z: number }
export interface GeometryObservationSourceDraft {
  source_name: string | null; source_reference: string | null; source_url: string | null;
  comment: string | null; retrieval_timestamp: string | null;
}
export interface BondLengthObservationDraft {
  id: string; atom1_id: string; atom2_id: string; value_angstrom: number;
  uncertainty_angstrom: number | null; equivalent_count: number; label: string | null;
  source: GeometryObservationSourceDraft | null;
}
export interface BondAngleObservationDraft {
  id: string; atom1_id: string; center_atom_id: string; atom2_id: string; value_deg: number;
  uncertainty_deg: number | null; equivalent_count: number; label: string | null;
  source: GeometryObservationSourceDraft | null;
}
export interface DihedralObservationDraft {
  id: string; atom1_id: string; atom2_id: string; atom3_id: string; atom4_id: string; value_deg: number;
  uncertainty_deg: number | null; equivalent_count: number; label: string | null;
  source: GeometryObservationSourceDraft | null;
}
export interface GeometryIdentityDraft {
  formula: string; charge: number; atom_inventory: Record<string, number>;
  inchi: string | null; inchikey: string | null; cas_rn: string | null; pubchem_cid: number | null;
  canonical_identity: string | null; curated_molecule_id: string | null; formula_identity_unambiguous: boolean;
}
export interface GeometrySourceDraft {
  name: string; reference: string | null; url: string | null; comments: string | null; retrieved_at: string | null;
}

export type GeometryEvidenceKind = "experimental" | "source_annotation" | "computed_conformer" | "deterministic_calculation" | "ideal_vsepr";

export interface MolecularGeometryEvidenceDraft {
  id: string;
  identity: GeometryIdentityDraft;
  evidence_type: GeometryEvidenceKind;
  atoms: GeometryAtomDraft[];
  bonds: GeometryBondDraft[];
  bond_lengths: BondLengthObservationDraft[];
  bond_angles: BondAngleObservationDraft[];
  dihedrals: DihedralObservationDraft[];
  coordinates: GeometryCoordinateDraft[] | null;
  units: "angstrom";
  phase: string | null;
  electronic_state: string | null;
  conformation: string | null;
  point_group: string | null;
  source: GeometrySourceDraft;
}

export interface MoleculeAdminListItem {
  id: string;
  formula: string;
  charge: number;
  name_vi: string;
  name_en: string;
  ax_en: string;
  molecular_geometry: string;
  molecular_geometry_vi: string;
  review_status: string;
  has_override: boolean;
  is_admin_added: boolean;
}

export interface MoleculeAdminRecord {
  molecule: MoleculeDraft;
  experimental_geometry: MolecularGeometryEvidenceDraft | null;
  properties: NormalizedProperty[];
  has_override: boolean;
  is_admin_added: boolean;
}

export interface ValidationIssue {
  severity: "error" | "warning" | "info";
  field: string | null;
  message_vi: string;
  message_en: string;
}

export interface ValidationReport {
  is_valid: boolean;
  errors: ValidationIssue[];
  warnings: ValidationIssue[];
  info: ValidationIssue[];
}

export interface MoleculeAdminSaveResponse {
  molecule: MoleculeAdminListItem;
  validation: ValidationReport;
  saved_at: string;
}

export interface CompletenessReport {
  molecule_id: string;
  missing_fields: string[];
  has_experimental_geometry: boolean;
  has_properties: boolean;
  review_status: string;
  completeness_percent: number;
}

export interface MoleculeAdminSavePayload {
  molecule: MoleculeDraft;
  experimental_geometry?: MolecularGeometryEvidenceDraft | null;
  properties?: NormalizedProperty[];
}
