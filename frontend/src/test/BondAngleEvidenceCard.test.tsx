import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import BondAngleEvidenceCard from "../components/vsepr/BondAngleEvidenceCard";
import PipelineSummary from "../components/workflow/PipelineSummary";
import { I18nProvider } from "../i18n";
import type { BondAngleEvidence, BondAnglesResult } from "../types/bondAngles";
import { waterAnalysis } from "./fixture";

const base: BondAngleEvidence = {
  id: "angle", atom1_element: "F", center_element: "N", atom2_element: "F",
  atom1_id: null, center_atom_id: null, atom2_id: null, value_deg: 102.37,
  display_label: "102.37°", evidence_type: "experimental", source_name: "NIST CCCBDB",
  source_url: "https://cccbdb.nist.gov/", reference: "1998Kuc", phase: "gas",
  uncertainty_deg: null, is_experimental: true, is_computed: false,
  is_approximate: false, equivalent_count: 3, coordinate_value_deg: 102.37,
  provenance_label_vi: "Phép đo thực nghiệm", provenance_label_en: "Experimental measurement",
};
const prediction: BondAngleEvidence = {
  ...base, id: "vsepr", value_deg: null, display_label: "<109.5°",
  evidence_type: "ideal_vsepr", source_name: "General VSEPR prediction",
  source_url: null, reference: null, phase: null, is_experimental: false,
  is_approximate: true,
};
function result(preferred: BondAngleEvidence): BondAnglesResult {
  return { preferred: [preferred], experimental: preferred.is_experimental ? [preferred] : [],
    coordinate_derived: [], curated_reference: [], vsepr_prediction: [prediction], selection_reason: "test" };
}
function renderCard(angles: BondAnglesResult, lang: "vi" | "en") {
  window.localStorage.setItem("vsepr-lang", lang);
  return render(<I18nProvider><BondAngleEvidenceCard angles={angles} notation="AX3E" /></I18nProvider>);
}

describe("BondAngleEvidenceCard", () => {
  beforeEach(() => window.localStorage.clear());

  it("shows experimental gas-phase provenance in Vietnamese", () => {
    renderCard(result(base), "vi");
    expect(screen.getByText("F–N–F: 102.37°")).toBeInTheDocument();
    expect(screen.getByText(/Thực nghiệm · pha khí/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "NIST CCCBDB" })).toHaveAttribute("href", "https://cccbdb.nist.gov/");
  });

  it("labels computed evidence as non-experimental in English", () => {
    const computed = { ...base, value_deg: 103.2, display_label: "103.20°",
      evidence_type: "computed_conformer" as const, source_name: "PubChem conformer",
      source_url: null, reference: null, phase: null, is_experimental: false, is_computed: true };
    renderCard(result(computed), "en");
    expect(screen.getByText(/Computed conformer · PubChem conformer/)).toBeInTheDocument();
    expect(screen.getByText("Computed value, not an experimental measurement.")).toBeInTheDocument();
  });

  it("returns null when only ideal VSEPR prediction exists", () => {
    const { container } = renderCard(result({ ...prediction, atom1_element: "H", atom2_element: "H" }), "en");
    expect(container).toBeEmptyDOMElement();
  });

  it("shows the NH3 experimental value", () => {
    renderCard(result({ ...base, atom1_element: "H", atom2_element: "H",
      value_deg: 106.67, display_label: "106.67°", reference: "1966Herzberg" }), "en");
    expect(screen.getByText("H–N–H: 106.67°")).toBeInTheDocument();
    expect(screen.getByText(/Experimental · gas phase/)).toBeInTheDocument();
  });

  it("uses preferred evidence in the pipeline summary", () => {
    window.localStorage.setItem("vsepr-lang", "en");
    const analysis = { ...waterAnalysis,
      molecule: { ...waterAnalysis.molecule, formula: "NF3", name_en: "Nitrogen trifluoride" },
      bond_angles: result(base) };
    render(<I18nProvider><PipelineSummary result={analysis} /></I18nProvider>);
    expect(screen.getByText("102.37°")).toBeInTheDocument();
  });

});
