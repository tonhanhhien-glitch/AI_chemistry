/** Mirrors `backend/app/properties/schema.py`. */

export type PropertyCategory = "identity" | "structural" | "physical" | "chemical";
export type PropertyEvidenceType = "experimental" | "source_annotation" | "computed" | "curated" | "deterministic";
export type PropertyApplicability = "applicable" | "not_applicable" | "unavailable";

export interface PropertyConditions {
  temperature: string | null;
  pressure: string | null;
  solvent: string | null;
  note: string | null;
}

export interface PropertyObservation {
  value: string | number;
  unit: string | null;
  uncertainty: string | number | null;
  temperature: string | null;
  pressure: string | null;
  phase: string | null;
  method: string | null;
  evidence_type: PropertyEvidenceType;
  source_name: string;
  source_reference: string | null;
  source_url: string | null;
  note: string | null;
}

export interface NormalizedProperty {
  key: string;
  category: PropertyCategory;
  label_vi: string;
  label_en: string;
  value: string | number | null;
  value_vi?: string | null;
  value_en?: string | null;
  unit: string | null;
  uncertainty: string | number | null;
  conditions: PropertyConditions | null;
  phase: string | null;
  evidence_type: PropertyEvidenceType;
  source_name: string;
  source_name_vi?: string | null;
  source_name_en?: string | null;
  source_reference: string | null;
  source_url: string | null;
  applicability: PropertyApplicability;
  retrieved_at: string | null;
  notes_vi: string | null;
  notes_en: string | null;
  observations?: PropertyObservation[];
}

export interface PropertyProviderStatus {
  provider: string;
  service: string;
  state: string;
  cache_hit: boolean;
  message: string | null;
}

export interface PropertyBundle {
  schema_version: "2.0";
  formula: string;
  charge: number;
  properties: NormalizedProperty[];
  statuses: PropertyProviderStatus[];
  /** True when a provider failed, so the table is known to be incomplete. */
  partial: boolean;
}
