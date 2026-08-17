import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import GeometryProvenanceBadge from "../components/viewer3d/GeometryProvenanceBadge";
import Molecule3DViewer from "../components/viewer3d/Molecule3DViewer";
import { I18nProvider } from "../i18n";
import type { Structure3D } from "../types/structure3d";
import { chlorineTrifluorideAnalysis, waterAnalysis } from "./fixture";

const mocks = vi.hoisted(() => ({ createViewer: vi.fn() }));
vi.mock("3dmol", () => ({ createViewer: mocks.createViewer }));

function viewerMock() {
  return {
    addModel: vi.fn(), zoomTo: vi.fn(), render: vi.fn(), clear: vi.fn(), setStyle: vi.fn(),
    addLabel: vi.fn(() => ({ kind: "label" })), removeLabel: vi.fn(),
    addLine: vi.fn(() => ({ kind: "line" })), addCurve: vi.fn(() => ({ kind: "curve" })),
    addSphere: vi.fn(() => ({ kind: "sphere" })), addCustom: vi.fn(() => ({ kind: "custom" })), removeShape: vi.fn(),
    setProjection: vi.fn(), getView: vi.fn(() => [1, 2, 3, -40, 0, 0, 0, 1]), setView: vi.fn(),
  };
}

function renderViewer(structure: Structure3D, lang: "vi" | "en" = "en") {
  window.localStorage.setItem("vsepr-lang", lang);
  const viewer = viewerMock();
  mocks.createViewer.mockReturnValue(viewer);
  render(<I18nProvider><Molecule3DViewer structure={structure} /></I18nProvider>);
  return viewer;
}

function renderBadge(structure: Structure3D, lang: "vi" | "en" = "en") {
  window.localStorage.setItem("vsepr-lang", lang);
  render(<I18nProvider><GeometryProvenanceBadge structure={structure} /></I18nProvider>);
}

describe("3D viewer provenance and angle view", () => {
  beforeEach(() => {
    Object.defineProperty(window, "WebGLRenderingContext", { configurable: true, value: function WebGLRenderingContext() {} });
    mocks.createViewer.mockReset();
    window.localStorage.clear();
  });

  it("uses an orthographic projection so on-screen angles are not foreshortened", () => {
    const viewer = renderViewer(waterAnalysis.structure3d);
    expect(mocks.createViewer).toHaveBeenCalledWith(expect.anything(), expect.objectContaining({ orthographic: true }));
    expect(viewer.setProjection).toHaveBeenCalledWith("orthographic");
  });

  it("shows an experimental source badge with the reference and phase", () => {
    renderBadge(chlorineTrifluorideAnalysis.structure3d);
    expect(screen.getByText("Experimental measurement")).toBeInTheDocument();
    expect(screen.getByText("NIST CCCBDB experimental gas-phase geometry")).toBeInTheDocument();
    expect(screen.getByText("1953Smith")).toBeInTheDocument();
    expect(screen.getByText("gas")).toBeInTheDocument();
    expect(screen.getByText(/Point group: C2v/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "NIST CCCBDB" })).toHaveAttribute("href", expect.stringContaining("cccbdb"));
  });

  it("says a coordinate set was fitted from the source's internal coordinates", () => {
    renderBadge(chlorineTrifluorideAnalysis.structure3d);
    expect(chlorineTrifluorideAnalysis.structure3d.geometry_evidence!.coordinates_are_fitted).toBe(true);
    expect(screen.getByText(/fitted from the source's internal coordinates/)).toBeInTheDocument();
  });

  it("labels an idealized model as a teaching illustration, never as a real angle", () => {
    renderBadge(waterAnalysis.structure3d);
    expect(screen.getByText("Idealized VSEPR illustration")).toBeInTheDocument();
    expect(screen.getByText(/teaching illustration/)).toBeInTheDocument();
    expect(screen.queryByText(/real angle/i)).not.toBeInTheDocument();
    expect(screen.queryByText("Experimental measurement")).not.toBeInTheDocument();
  });

  it("labels a computed conformer as computed", () => {
    const computed: Structure3D = {
      ...waterAnalysis.structure3d,
      source: "pubchem_3d", source_label: "PubChem 3D conformer",
      evidence_type: "computed_conformer", is_computed: true, is_illustrative: false, is_experimental: false,
      geometry_evidence: {
        ...waterAnalysis.structure3d.geometry_evidence!,
        evidence_type: "computed_conformer", provider: "pubchem_3d", source_name: "PubChem",
        is_computed: true, is_ideal: false, is_experimental: false,
        provenance_label_vi: "Cấu dạng tính toán", provenance_label_en: "Computed conformer",
      },
    };
    renderBadge(computed);
    expect(screen.getByText("Computed conformer")).toBeInTheDocument();
    expect(screen.getByText(/not an experimental measurement/)).toBeInTheDocument();
  });

  it("lists every inequivalent angle in the selector with its equivalent count", async () => {
    renderViewer(chlorineTrifluorideAnalysis.structure3d);
    const selector = screen.getByRole("combobox", { name: /Select atom triplet/ });
    const options = Array.from(selector.querySelectorAll("option")).map((option) => option.textContent);
    expect(options).toHaveLength(2);
    expect(options[0]).toContain("87.45°");
    expect(options[0]).toContain("×2");
    expect(options[1]).toContain("174.90°");
    expect(options[1]).not.toContain("×");
    await userEvent.selectOptions(selector, chlorineTrifluorideAnalysis.structure3d.angle_annotations[1].id);
    expect((selector as HTMLSelectElement).value).toBe(chlorineTrifluorideAnalysis.structure3d.angle_annotations[1].id);
  });

  it("aligns the camera perpendicular to the selected angle's plane", async () => {
    const viewer = renderViewer(chlorineTrifluorideAnalysis.structure3d);
    await userEvent.click(screen.getByRole("button", { name: "View selected angle" }));
    await waitFor(() => expect(viewer.setView).toHaveBeenCalled());
    const spec = viewer.setView.mock.calls[0][0] as number[];
    expect(spec).toHaveLength(8);
    // Translation and zoom are preserved; only the rotation quaternion changes.
    expect(spec.slice(0, 4)).toEqual([1, 2, 3, -40]);
    expect(Math.hypot(spec[4], spec[5], spec[6], spec[7])).toBeCloseTo(1, 8);
  });

  it("realigns to whichever angle is selected", async () => {
    const viewer = renderViewer(chlorineTrifluorideAnalysis.structure3d);
    const selector = screen.getByRole("combobox", { name: /Select atom triplet/ });
    await userEvent.click(screen.getByRole("button", { name: "View selected angle" }));
    const first = (viewer.setView.mock.calls[0][0] as number[]).slice(4);
    await userEvent.selectOptions(selector, chlorineTrifluorideAnalysis.structure3d.angle_annotations[1].id);
    await userEvent.click(screen.getByRole("button", { name: "View selected angle" }));
    const second = (viewer.setView.mock.calls[1][0] as number[]).slice(4);
    expect(second).not.toEqual(first);
  });

  it("keeps rotate/zoom/reset interaction available", async () => {
    const viewer = renderViewer(waterAnalysis.structure3d);
    viewer.zoomTo.mockClear();
    await userEvent.click(screen.getByRole("button", { name: "Reset" }));
    expect(viewer.zoomTo).toHaveBeenCalled();
  });

  it("displays the angle labels the backend computed from the rendered coordinates", async () => {
    const viewer = renderViewer(chlorineTrifluorideAnalysis.structure3d);
    await waitFor(() => expect(viewer.addLabel).toHaveBeenCalledWith("87.45°", expect.any(Object)));
    // 90 deg is the AX3E2 idealization; it must not be drawn over experimental coordinates.
    expect(viewer.addLabel).not.toHaveBeenCalledWith("90.0°", expect.any(Object));
  });
});
