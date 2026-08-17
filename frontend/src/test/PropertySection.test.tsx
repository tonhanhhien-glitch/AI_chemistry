import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import PropertySection from "../components/properties/PropertySection";
import PropertyTable from "../components/properties/PropertyTable";
import { I18nProvider } from "../i18n";
import type { NormalizedProperty, PropertyBundle } from "../types/properties";
import { fetchProperties } from "../api/propertiesApi";
import { waterAnalysis } from "./fixture";

vi.mock("../api/propertiesApi", () => ({ fetchProperties: vi.fn() }));

function property(overrides: Partial<NormalizedProperty> = {}): NormalizedProperty {
  return {
    key: "molar_mass", category: "physical", label_vi: "Khối lượng mol", label_en: "Molar mass",
    value: 18.015, unit: "g/mol", uncertainty: null, conditions: null, phase: null,
    evidence_type: "computed", source_name: "Standard atomic weights (IUPAC)",
    source_reference: null, source_url: null, applicability: "applicable",
    retrieved_at: null, notes_vi: null, notes_en: null,
    ...overrides,
  };
}

function bundle(properties: NormalizedProperty[], overrides: Partial<PropertyBundle> = {}): PropertyBundle {
  return {
    schema_version: "2.0", formula: "H2O", charge: 0, properties,
    statuses: [], partial: false, ...overrides,
  };
}

function renderTable(properties: NormalizedProperty[], extra: Partial<PropertyBundle> = {}, lang: "vi" | "en" = "en") {
  window.localStorage.setItem("vsepr-lang", lang);
  const data = bundle(properties, extra);
  return render(<I18nProvider><PropertyTable properties={data.properties} statuses={data.statuses} partial={data.partial} /></I18nProvider>);
}

function renderSection(lang: "vi" | "en" = "en") {
  window.localStorage.setItem("vsepr-lang", lang);
  return render(
    <I18nProvider>
      <PropertySection molecule={waterAnalysis.molecule} inlineProperties={waterAnalysis.properties} />
    </I18nProvider>,
  );
}

describe("PropertyTable", () => {
  beforeEach(() => window.localStorage.clear());

  it("groups properties by category with bilingual labels", () => {
    renderTable([
      property({ key: "formula", category: "identity", label_en: "Formula", value: "H2O" }),
      property({ key: "ax_en", category: "structural", label_en: "AXnEm notation", value: "AX2E2" }),
      property(),
      property({ key: "polarity", category: "chemical", label_en: "Polarity note", value: "Polar" }),
    ]);
    expect(screen.getByRole("heading", { name: "Identity" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Structural" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Physical" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Chemical" })).toBeInTheDocument();
    expect(screen.getByText("18.015 g/mol")).toBeInTheDocument();
  });

  it("switches labels with the language", () => {
    renderTable([property()], {}, "vi");
    expect(screen.getByText("Khối lượng mol")).toBeInTheDocument();
  });

  it("shows the evidence type and source for every value", () => {
    renderTable([
      property({ key: "melting_point", value: "0 °C", unit: null, evidence_type: "experimental",
        source_name: "PubChem", source_reference: "Ref 1", source_url: "https://pubchem.example/962" }),
    ]);
    expect(screen.getByText(/Experimental · /)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "PubChem" })).toHaveAttribute("href", "https://pubchem.example/962");
    expect(screen.getByText(/Ref 1/)).toBeInTheDocument();
  });

  it("shows conditions and phase alongside a measurement", () => {
    renderTable([
      property({ key: "density", value: "1.0", unit: "g/cm³", evidence_type: "experimental",
        source_name: "PubChem", phase: "liquid",
        conditions: { temperature: "20 °C", pressure: "101 kPa", solvent: null, note: null } }),
    ]);
    expect(screen.getByText(/20 °C · 101 kPa · liquid/)).toBeInTheDocument();
  });

  it("renders a not-applicable ion property as such, with its reason and no value", () => {
    renderTable([
      property({
        key: "melting_point", label_en: "Melting point", value: null, unit: null,
        evidence_type: "deterministic", source_name: "PubChem", applicability: "not_applicable",
        notes_en: "This is a bulk-substance property. An isolated molecular ion has no value of its own.",
      }),
    ]);
    const row = screen.getByText("Melting point").closest("tr")!;
    expect(row).toHaveAttribute("data-applicability", "not_applicable");
    expect(screen.getByText("Not applicable to this species")).toBeInTheDocument();
    expect(screen.getByText(/isolated molecular ion has no value of its own/)).toBeInTheDocument();
  });

  it("renders missing data as missing rather than inventing a number", () => {
    renderTable([
      property({ key: "polarity", label_en: "Polarity note", value: null, unit: null,
        applicability: "unavailable", evidence_type: "deterministic", source_name: "Deterministic chemistry engine",
        notes_en: "Polarity is not inferred for an uncurated record." }),
    ]);
    expect(screen.getByText("No data available")).toBeInTheDocument();
    expect(screen.queryByText(/undefined|null|NaN|0 °C/)).not.toBeInTheDocument();
  });

  it("warns when an external provider failed, without hiding the rest", () => {
    renderTable(
      [property()],
      { partial: true, statuses: [{ provider: "pubchem_view", service: "PubChem View", state: "timeout", cache_hit: false, message: null }] },
    );
    expect(screen.getByRole("status")).toHaveTextContent(/incomplete because an external source failed/);
    expect(screen.getByRole("status")).toHaveTextContent("PubChem View: timeout");
    expect(screen.getByText("18.015 g/mol")).toBeInTheDocument();
  });

  it("says so when there is nothing to show", () => {
    renderTable([]);
    expect(screen.getByText("No properties are available for this species.")).toBeInTheDocument();
  });
});

describe("PropertySection lazy loading", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.mocked(fetchProperties).mockReset();
  });

  it("renders the inline computed properties immediately, then the loaded bundle", async () => {
    let resolve: (value: PropertyBundle) => void = () => undefined;
    vi.mocked(fetchProperties).mockReturnValue(new Promise<PropertyBundle>((done) => { resolve = done; }));
    renderSection();

    // The locally computed properties from /analyze are on screen before the fetch settles.
    expect(screen.getByRole("heading", { name: "Identity" })).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Loading properties from external sources…");

    resolve(bundle([property({ key: "melting_point", label_en: "Melting point", value: "0 °C", unit: null, evidence_type: "experimental", source_name: "PubChem" })]));
    expect(await screen.findByText("Melting point")).toBeInTheDocument();
    expect(screen.getByText("0 °C")).toBeInTheDocument();
  });

  it("requests properties from the dedicated endpoint, not from /analyze", async () => {
    vi.mocked(fetchProperties).mockResolvedValue(bundle([property()]));
    renderSection();
    await waitFor(() => expect(fetchProperties).toHaveBeenCalledTimes(1));
    expect(fetchProperties).toHaveBeenCalledWith(
      expect.objectContaining({ molecule_id: waterAnalysis.molecule.id }),
      expect.any(AbortSignal),
    );
  });

  it("keeps the analysis usable when the external lookup fails, and offers a retry", async () => {
    vi.mocked(fetchProperties).mockRejectedValueOnce(new Error("network down"));
    renderSection();
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("Could not load properties from external sources.");
    // The locally computed table is still rendered beside the error.
    expect(screen.getByRole("heading", { name: "Identity" })).toBeInTheDocument();

    vi.mocked(fetchProperties).mockResolvedValueOnce(bundle([property({ key: "xlogp", label_en: "XLogP", value: -0.5, unit: null })]));
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(await screen.findByText("XLogP")).toBeInTheDocument();
  });

  it("surfaces a partial bundle produced by a failing provider", async () => {
    vi.mocked(fetchProperties).mockResolvedValue(bundle(
      [property()],
      { partial: true, statuses: [{ provider: "pubchem_rest", service: "PubChem", state: "temporary_failure", cache_hit: false, message: null }] },
    ));
    renderSection();
    expect(await screen.findByText(/PubChem: temporary_failure/)).toBeInTheDocument();
  });
});
