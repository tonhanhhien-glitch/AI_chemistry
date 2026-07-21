import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
vi.mock("3dmol", () => ({ createViewer: vi.fn() }));
import AnalysisPage from "../pages/AnalysisPage";
import { analyzeMolecule } from "../api/analysisApi";
import { waterAnalysis } from "./fixture";

vi.mock("../api/analysisApi", () => ({ analyzeMolecule: vi.fn() }));
vi.mock("../api/moleculeApi", () => ({ searchMolecules: vi.fn(async () => []) }));

function renderPage() { return render(<MemoryRouter initialEntries={["/analysis"]}><AnalysisPage /></MemoryRouter>); }

describe("AnalysisPage", () => {
  beforeEach(() => vi.mocked(analyzeMolecule).mockReset());
  it("validates an empty input in Vietnamese", async () => { renderPage(); await userEvent.click(screen.getByRole("button", { name: "Phân tích" })); expect(screen.getByRole("alert")).toHaveTextContent("Vui lòng nhập"); });
  it("renders the full offline analysis and WebGL fallback", async () => { vi.mocked(analyzeMolecule).mockResolvedValue(waterAnalysis); renderPage(); await userEvent.type(screen.getByLabelText("Công thức hoặc tên chất"), "H2O"); await userEvent.click(screen.getByRole("button", { name: "Phân tích" })); expect(await screen.findByRole("heading", { name: "Cấu trúc Lewis", level: 2 })).toBeInTheDocument(); expect(screen.getAllByText("AX2E2").length).toBeGreaterThan(0); expect(screen.getByText(/Trình duyệt không thể khởi tạo WebGL/)).toBeInTheDocument(); expect(screen.getByText("Claude chưa cấu hình.")).toBeInTheDocument(); });
});
