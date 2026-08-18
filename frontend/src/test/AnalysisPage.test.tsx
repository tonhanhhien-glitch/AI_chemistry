import { render, screen } from "@testing-library/react";
import { AxiosError, type AxiosResponse } from "axios";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
vi.mock("3dmol", () => ({ createViewer: vi.fn() }));
import AnalysisPage from "../pages/AnalysisPage";
import { analyzeMolecule } from "../api/analysisApi";
import { fetchProperties } from "../api/propertiesApi";
import { waterAnalysis } from "./fixture";

vi.mock("../api/analysisApi", () => ({ analyzeMolecule: vi.fn() }));
vi.mock("../api/moleculeApi", () => ({ searchMolecules: vi.fn(async () => []) }));
vi.mock("../api/propertiesApi", () => ({ fetchProperties: vi.fn() }));

function renderPage() { return render(<MemoryRouter initialEntries={["/analysis"]}><AnalysisPage /></MemoryRouter>); }

describe("AnalysisPage", () => {
  beforeEach(() => { vi.mocked(analyzeMolecule).mockReset(); vi.mocked(fetchProperties).mockReset(); });
  it("validates an empty input in Vietnamese", async () => { renderPage(); await userEvent.click(screen.getByRole("button", { name: "Tìm" })); expect(screen.getByRole("alert")).toHaveTextContent("Vui lòng nhập"); });
  it("renders the full offline analysis and WebGL fallback", async () => { vi.mocked(analyzeMolecule).mockResolvedValue(waterAnalysis); renderPage(); await userEvent.type(screen.getByLabelText("Công thức hoặc tên chất"), "H2O"); await userEvent.click(screen.getByRole("button", { name: "Tìm" })); expect(await screen.findByRole("heading", { name: "Cấu trúc Lewis", level: 2 })).toBeInTheDocument(); expect(screen.getAllByText((_, element) => element?.textContent === "AX2E2").length).toBeGreaterThan(0); /* AX2E2's "2"s render as subscript elements, splitting the text across nodes */ expect(screen.getByText(/Trình duyệt không thể khởi tạo WebGL/)).toBeInTheDocument(); });
  it("resubmits an ambiguous PubChem formula with the selected CID", async () => {
    const response = { data: { detail: { code: "AMBIGUOUS_MOLECULE", message: "Chọn chất.", candidates: [{ id: "pubchem:1", cid: 1, formula: "NF3", charge: 0, name_vi: "Nitrogen trifluoride A", name_en: "Nitrogen trifluoride A", canonical_smiles: "N(F)(F)F", source: "PubChem" }] } }, status: 409, statusText: "Conflict", headers: {}, config: {} } as AxiosResponse;
    vi.mocked(analyzeMolecule).mockRejectedValueOnce(new AxiosError("ambiguous", "409", undefined, undefined, response)).mockResolvedValueOnce(waterAnalysis);
    renderPage();
    await userEvent.type(screen.getByLabelText("Công thức hoặc tên chất"), "NF3");
    await userEvent.click(screen.getByRole("button", { name: "Tìm" }));
    const candidate = await screen.findByRole("button", { name: /Nitrogen trifluoride A/ });
    expect(candidate).toHaveTextContent("CID 1");
    await userEvent.click(candidate);
    await screen.findByRole("heading", { name: "Cấu trúc Lewis", level: 2 });
    expect(analyzeMolecule).toHaveBeenLastCalledWith(expect.objectContaining({ query: "NF3", pubchem_cid: 1 }), expect.any(AbortSignal));
  });
});
