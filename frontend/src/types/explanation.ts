export type ExplanationLevel = "basic" | "intermediate" | "advanced";

export interface ExplanationSections {
  lewis: string;
  ax_en: string;
  electron_geometry: string;
  molecular_geometry: string;
  structure_property: string;
  learning_tip: string;
  disclaimer: string;
}

export interface Explanation {
  formula: string;
  level: ExplanationLevel;
  language: "vi" | "en";
  sections: ExplanationSections;
  source: "claude" | "deterministic_fallback";
  fallback_reason: string | null;
  prompt_version: string;
  facts_validated: boolean;
}
