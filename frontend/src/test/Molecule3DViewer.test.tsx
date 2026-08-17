import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Molecule3DViewer from "../components/viewer3d/Molecule3DViewer";
import type { Structure3D } from "../types/structure3d";
import { waterAnalysis } from "./fixture";

const mocks = vi.hoisted(() => ({ createViewer: vi.fn() }));
vi.mock("3dmol", () => ({ createViewer: mocks.createViewer }));

type ShapeSpecMock = { color?: string; opacity?: number; vertexArr?: unknown[]; normalArr?: unknown[]; faceArr?: number[] };
type Point3D = { x: number; y: number; z: number };

function viewerMock() {
  return {
    addModel: vi.fn(), zoomTo: vi.fn(), render: vi.fn(), clear: vi.fn(), setStyle: vi.fn(),
    addLabel: vi.fn(() => ({ kind: "label" })), removeLabel: vi.fn(),
    addLine: vi.fn(() => ({ kind: "line" })), addCurve: vi.fn((spec: { points: Point3D[] }) => ({ kind: "curve", spec })),
    addSphere: vi.fn((spec: ShapeSpecMock) => ({ kind: "sphere", spec })), addCustom: vi.fn((spec: ShapeSpecMock) => ({ kind: "custom", spec })), removeShape: vi.fn(),
    setProjection: vi.fn(), getView: vi.fn(() => [0, 0, 0, -50, 0, 0, 0, 1]), setView: vi.fn(),
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
    ["coordinates", "mol"], ["sdf", "sdf"], ["molblock", "mol"], ["pdb", "pdb"],
  ] as const)("passes %s responses to 3Dmol as %s", async (input, expected) => {
    const viewer = viewerMock(); mocks.createViewer.mockReturnValue(viewer);
    render(<Molecule3DViewer structure={structure(input)} />);
    await waitFor(() => expect(viewer.addModel).toHaveBeenCalled());
    expect(viewer.addModel.mock.calls[0][1]).toBe(expected);
    if (input === "coordinates") expect(viewer.addModel.mock.calls[0][0]).toContain("V2000");
    else expect(viewer.addModel.mock.calls[0][0]).toBe(structure(input).data);
  });

  it("serializes the engine's explicit bonds so 3Dmol never re-derives them by distance", async () => {
    const viewer = viewerMock(); mocks.createViewer.mockReturnValue(viewer);
    render(<Molecule3DViewer structure={structure("coordinates")} />);
    await waitFor(() => expect(viewer.addModel).toHaveBeenCalled());
    const lines = (viewer.addModel.mock.calls[0][0] as string).split("\n");
    expect(lines[3]).toBe("  3  2  0  0  0  0  0  0  0  0999 V2000");
    // V2000 is column-positional: element at 31-34, bond serials at 0-3 and 3-6.
    const atoms = structure("coordinates").atoms;
    expect(lines.slice(4, 7).map((line) => line.substring(31, 34).trim())).toEqual(atoms.map((atom) => atom.element));
    expect(lines.slice(4, 7).map((line) => parseFloat(line.substring(0, 10)))).toEqual(atoms.map((atom) => Number(atom.x.toFixed(4))));
    expect(lines.slice(7, 9).map((line) => [line.substring(0, 3), line.substring(3, 6), line.substring(6, 9)].map(Number))).toEqual([[1, 2, 1], [1, 3, 1]]);
    expect(lines).toContain("M  END");
  });

  it("falls back to xyz only when the engine supplies no connectivity", async () => {
    const viewer = viewerMock(); mocks.createViewer.mockReturnValue(viewer);
    render(<Molecule3DViewer structure={{ ...structure("coordinates"), bonds: [] }} />);
    await waitFor(() => expect(viewer.addModel).toHaveBeenCalled());
    expect(viewer.addModel.mock.calls[0][1]).toBe("xyz");
  });

  it.each([
    ["ball-and-stick", { stick: { radius: 0.15 }, sphere: { scale: 0.3 } }],
    ["stick", { stick: { radius: 0.18 } }],
    ["space-filling", { sphere: { scale: 0.95 } }],
  ] as const)("draws %s with its own primitives", async (option, expected) => {
    const viewer = viewerMock(); mocks.createViewer.mockReturnValue(viewer);
    render(<Molecule3DViewer structure={structure("coordinates")} />);
    await userEvent.selectOptions(screen.getByRole("combobox", { name: /Kiểu hiển thị/ }), option);
    await waitFor(() => expect(viewer.setStyle).toHaveBeenLastCalledWith({}, expected));
  });

  it("keeps the ball-and-stick sticks thick enough to stay visible", () => {
    const viewer = viewerMock(); mocks.createViewer.mockReturnValue(viewer);
    render(<Molecule3DViewer structure={structure("coordinates")} />);
    const [, spec] = viewer.setStyle.mock.calls[0] as [unknown, { stick?: { radius: number }; sphere?: { scale: number } }];
    expect(spec.stick!.radius).toBeGreaterThanOrEqual(0.1);
    expect(spec.stick!.radius).toBeLessThanOrEqual(0.16);
    expect(spec.sphere!.scale).toBeGreaterThanOrEqual(0.25);
    expect(spec.sphere!.scale).toBeLessThanOrEqual(0.35);
  });

  it("labels the arc with the molecule-specific angle the summary uses, not the VSEPR ideal", async () => {
    const viewer = viewerMock(); mocks.createViewer.mockReturnValue(viewer);
    render(<Molecule3DViewer structure={structure("coordinates")} />);
    await userEvent.click(screen.getByRole("checkbox", { name: "Góc liên kết" }));
    await waitFor(() => expect(viewer.addCurve).toHaveBeenCalled());
    expect(viewer.addLabel).toHaveBeenCalledWith("104.5°", expect.any(Object));
    expect(viewer.addLabel).not.toHaveBeenCalledWith("109.5°", expect.any(Object));
    await userEvent.click(screen.getByRole("checkbox", { name: "Góc liên kết" }));
    expect(viewer.removeShape).toHaveBeenCalled();
  });

  it("draws the arc between the two O-H bond vectors with O as the vertex", async () => {
    const viewer = viewerMock(); mocks.createViewer.mockReturnValue(viewer);
    render(<Molecule3DViewer structure={structure("coordinates")} />);
    await userEvent.click(screen.getByRole("checkbox", { name: "Góc liên kết" }));
    await waitFor(() => expect(viewer.addCurve).toHaveBeenCalled());
    const [oxygen, first, second] = structure("coordinates").atoms;
    const points = viewer.addCurve.mock.calls[0]![0].points;
    const bearing = (point: Point3D, atom: Point3D) => {
      const arc = Math.hypot(point.x - oxygen.x, point.y - oxygen.y, point.z - oxygen.z);
      const bond = Math.hypot(atom.x - oxygen.x, atom.y - oxygen.y, atom.z - oxygen.z);
      const dot = (point.x - oxygen.x) * (atom.x - oxygen.x) + (point.y - oxygen.y) * (atom.y - oxygen.y) + (point.z - oxygen.z) * (atom.z - oxygen.z);
      return (Math.acos(Math.max(-1, Math.min(1, dot / (arc * bond)))) * 180) / Math.PI;
    };
    expect(bearing(points[0], first)).toBeCloseTo(0, 3);
    expect(bearing(points[points.length - 1], second)).toBeCloseTo(0, 3);
    expect(bearing(points[0], second)).toBeCloseTo(104.5, 1);
  });

  it("shows and removes illustrative lone-pair shapes", async () => {
    const viewer = viewerMock(); mocks.createViewer.mockReturnValue(viewer);
    render(<Molecule3DViewer structure={structure("coordinates")} />);
    await userEvent.click(screen.getByRole("checkbox", { name: "Miền cặp e tự do" }));
    await waitFor(() => expect(viewer.addSphere).toHaveBeenCalledTimes(4));
    expect(screen.getByText(/Các thùy cặp electron tự do là vùng minh họa/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("checkbox", { name: "Miền cặp e tự do" }));
    expect(viewer.removeShape).toHaveBeenCalled();
  });

  it("draws one translucent domain lobe holding two opaque red electrons per lone pair", async () => {
    const viewer = viewerMock(); mocks.createViewer.mockReturnValue(viewer);
    render(<Molecule3DViewer structure={structure("coordinates")} />);
    // H2O has two lone pairs: one translucent lobe each, two opaque electrons per lobe.
    await waitFor(() => expect(viewer.addCustom).toHaveBeenCalledTimes(2));
    const lobe = viewer.addCustom.mock.calls[0]![0];
    expect(lobe.color).toBe("#8edff2"); expect(lobe.opacity).toBeLessThan(0.4); expect(lobe.opacity).toBeGreaterThan(0.15);
    expect(lobe.faceArr!.length % 3).toBe(0); expect(lobe.normalArr).toHaveLength(lobe.vertexArr!.length);
    expect(viewer.addSphere).toHaveBeenCalledTimes(4);
    viewer.addSphere.mock.calls.forEach(([sphere]) => { expect(sphere.color).toBe("#ff1a1a"); expect(sphere.opacity).toBe(1); });
  });
});
