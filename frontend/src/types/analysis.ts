import type { Explanation, ExplanationLevel } from "./explanation";
import type { LewisStructure } from "./lewis";
import type { Molecule, PropertyItem } from "./molecule";
import type { Structure3D } from "./structure3d";
import type { VseprResult } from "./vsepr";

export interface AnalysisRequest {
  formula?: string;
  molecule_id?: string;
  include_explanation?: boolean;
  explanation_level?: ExplanationLevel;
  language?: "vi" | "en";
}

export interface AnalysisResult {
  schema_version: "1.0";
  molecule: Molecule;
  lewis: LewisStructure;
  vsepr: VseprResult;
  properties: PropertyItem[];
  structure3d: Structure3D;
  explanation: Explanation | null;
  notices: {
    offline_capable: boolean;
    external_services_used: string[];
    warnings_vi: string[];
  };
}
