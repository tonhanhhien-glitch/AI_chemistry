import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Molecule3DViewer from "../components/viewer3d/Molecule3DViewer";
import type { Structure3D } from "../types/structure3d";
import { waterAnalysis } from "./fixture";

const mocks = vi.hoisted(() => ({ createViewer: vi.fn() }));
vi.mock("3dmol", () => ({ createViewer: mocks.createViewer }));

function viewerMock() {
  return {
    addModel: vi.fn(), zoomTo: vi.fn(), render: vi.fn(), clear: vi.fn(), setStyle: vi.fn(),
    addLabel: vi.fn(() => ({ kind: "label" })), removeLabel: vi.fn(),
    addLine: vi.fn(() => ({ kind: "line" })), addCurve: vi.fn(() => ({ kind: "curve" })),
    addSphere: vi.fn(() => ({ kind: "sphere" })), removeShape: vi.fn(),
  };
}

function structure(format: Structure3D["format"]): Structure3D {
  const base = waterAnalysis.structure3d;
  if (format === "coordinates") return { ...base, format, data: null };
  return { ...base, format, data: format === "pdb" ? "ATOM PDB" : "MOLECULE DATA" };
}

describe("Molecule3DViewer", () => {
  beforeEach(() => {
    Object.defineProperty(window, "WebGLRenderingContext", { configurable: true, value: function WebGLRenderingContext() {} });
    mocks.createViewer.mockReset();
  });

  it.each([
    ["coordinates", "xyz"], ["sdf", "sdf"], ["molblock", "mol"], ["pdb", "pdb"],
  ] as const)("passes %s responses to 3Dmol as %s", async (input, expected) => {
    const viewer = viewerMock(); mocks.createViewer.mockReturnValue(viewer);
    render(<Molecule3DViewer structure={structure(input)} />);
    await waitFor(() => expect(viewer.addModel).toHaveBeenCalled());
    expect(viewer.addModel.mock.calls[0][1]).toBe(expected);
    if (input === "coordinates") expect(viewer.addModel.mock.calls[0][0]).toContain("O 0 0 0");
    else expect(viewer.addModel.mock.calls[0][0]).toBe(structure(input).data);
  });

  it("shows and removes a coordinate-derived angle overlay", async () => {
    const viewer = viewerMock(); mocks.createViewer.mockReturnValue(viewer);
    render(<Molecule3DViewer structure={structure("coordinates")} />);
    await userEvent.click(screen.getByRole("checkbox", { name: "Góc liên kết" }));
    await waitFor(() => expect(viewer.addCurve).toHaveBeenCalled());
    expect(viewer.addLabel).toHaveBeenCalledWith("109.5°", expect.any(Object));
    expect(screen.getByText(/Góc từ tọa độ hiển thị.*109.5°/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("checkbox", { name: "Góc liên kết" }));
    expect(viewer.removeShape).toHaveBeenCalled();
  });

  it("shows and removes illustrative lone-pair shapes", async () => {
    const viewer = viewerMock(); mocks.createViewer.mockReturnValue(viewer);
    render(<Molecule3DViewer structure={structure("coordinates")} />);
    await userEvent.click(screen.getByRole("checkbox", { name: "Miền cặp e tự do" }));
    await waitFor(() => expect(viewer.addSphere).toHaveBeenCalledTimes(2));
    expect(screen.getByText(/Các thùy cặp electron tự do là vùng minh họa/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("checkbox", { name: "Miền cặp e tự do" }));
    expect(viewer.removeShape).toHaveBeenCalled();
  });

  it("displays the structure provenance badge", () => {
    const viewer = viewerMock(); mocks.createViewer.mockReturnValue(viewer);
    render(<Molecule3DViewer structure={{ ...structure("sdf"), source: "pubchem_3d", source_label: "PubChem 3D conformer" }} />);
    expect(screen.getByText("PubChem 3D conformer")).toBeInTheDocument();
  });
});
