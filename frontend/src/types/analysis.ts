import type { BondAnglesResult } from "./bondAngles";
import type { Explanation, ExplanationLevel } from "./explanation";
import type { LewisStructure } from "./lewis";
import type { Molecule } from "./molecule";
import type { NormalizedProperty } from "./properties";
import type { Structure3D } from "./structure3d";
import type { VseprResult } from "./vsepr";

export interface AnalysisRequest {
  /** Raw chemical query -- a formula or a name. The backend decides which. */
  query?: string;
  formula?: string;
  molecule_id?: string;
  pubchem_cid?: number;
  include_explanation?: boolean;
  explanation_level?: ExplanationLevel;
  language?: "vi" | "en";
}

/** Mirrors `ExternalServiceName` in `backend/app/schemas/molecule_schema.py`. */
export type ExternalServiceName =
  | "PubChem"
  | "PubChem View"
  | "RDKit"
  | "NIST CCCBDB"
  | "Local geometry snapshot"
  | "Deterministic chemistry";

export interface AnalysisResult {
  schema_version: "1.1";
  molecule: Molecule;
  lewis: LewisStructure;
  vsepr: VseprResult;
  properties: NormalizedProperty[];
  structure3d: Structure3D;
  bond_angles: BondAnglesResult;
  explanation: Explanation | null;
  notices: {
    offline_capable: boolean;
    external_services_used: string[];
    warnings_vi: string[];
    warnings_en: string[];
    external_service_statuses: Array<{ service: ExternalServiceName; state: string; cache_hit: boolean; message: string | null }>;
  };
}
