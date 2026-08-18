import { render, screen, waitFor } from "@testing-library/react";
import { AxiosError, type AxiosResponse } from "axios";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("3dmol", () => ({ createViewer: vi.fn() }));

import MoleculeDataPage from "../pages/MoleculeDataPage";
import {
  adminLogin, adminLogout, adminSession, getAdminMolecule, listAdminMolecules,
  previewAdminMolecule, updateAdminMolecule, validateAdminMolecule,
} from "../api/moleculeAdminApi";
import { waterAnalysis } from "./fixture";
import type { MoleculeAdminListItem, MoleculeAdminRecord } from "../types/moleculeAdmin";
import { emptyMoleculeDraft } from "../components/moleculeData/defaults";

vi.mock("../api/moleculeAdminApi", () => ({
  adminLogin: vi.fn(),
  adminLogout: vi.fn(),
  adminSession: vi.fn(),
  listAdminMolecules: vi.fn(),
  getAdminMolecule: vi.fn(),
  createAdminMolecule: vi.fn(),
  updateAdminMolecule: vi.fn(),
  validateAdminMolecule: vi.fn(),
  previewAdminMolecule: vi.fn(),
  revertAdminMolecule: vi.fn(),
  getAdminCompleteness: vi.fn(),
  generateAdminDraft: vi.fn(),
}));

// The UI defaults to Vietnamese (see i18n/index.tsx), so queries below use the
// Vietnamese strings -- same convention as AnalysisPage.test.tsx.

const nh3Draft = { ...emptyMoleculeDraft(), id: "nh3", formula: "NH3", charge: 0, name_en: "Ammonia", name_vi: "Ammonia" };
const nh3ListItem: MoleculeAdminListItem = {
  id: "nh3", formula: "NH3", charge: 0, name_vi: "Ammonia", name_en: "Ammonia",
  ax_en: "AX3E", molecular_geometry: "trigonal pyramidal", molecular_geometry_vi: "chóp tam giác",
  review_status: "internal_golden_pending_expert_signoff", has_override: false, is_admin_added: false,
};
const nh3Record: MoleculeAdminRecord = {
  molecule: nh3Draft, experimental_geometry: null, properties: [], has_override: false, is_admin_added: false,
};

function renderPage() {
  return render(<MemoryRouter initialEntries={["/admin"]}><MoleculeDataPage /></MemoryRouter>);
}

describe("MoleculeDataPage", () => {
  beforeEach(() => {
    vi.mocked(adminLogin).mockReset();
    vi.mocked(adminLogout).mockReset();
    vi.mocked(adminSession).mockReset();
    vi.mocked(listAdminMolecules).mockReset().mockResolvedValue([nh3ListItem]);
    vi.mocked(getAdminMolecule).mockReset().mockResolvedValue(nh3Record);
    vi.mocked(validateAdminMolecule).mockReset();
    vi.mocked(previewAdminMolecule).mockReset();
    vi.mocked(updateAdminMolecule).mockReset();
  });

  it("shows the login form when not authenticated", async () => {
    vi.mocked(adminSession).mockResolvedValue({ authenticated: false, username: null });
    renderPage();
    expect(await screen.findByRole("heading", { name: "Quản trị dữ liệu phân tử" })).toBeInTheDocument();
  });

  it("shows an error on invalid login", async () => {
    vi.mocked(adminSession).mockResolvedValue({ authenticated: false, username: null });
    const response = { data: { detail: "Sai tên đăng nhập hoặc mật khẩu." }, status: 401, statusText: "Unauthorized", headers: {}, config: {} } as AxiosResponse;
    vi.mocked(adminLogin).mockRejectedValue(new AxiosError("invalid credentials", "401", undefined, undefined, response));
    renderPage();
    await screen.findByRole("heading", { name: "Quản trị dữ liệu phân tử" });
    await userEvent.type(screen.getByLabelText("Tên đăng nhập"), "admin");
    await userEvent.type(screen.getByLabelText("Mật khẩu"), "wrong");
    await userEvent.click(screen.getByRole("button", { name: "Đăng nhập" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/Sai/);
  });

  it("logs in successfully and shows the molecule list", async () => {
    vi.mocked(adminSession).mockResolvedValue({ authenticated: false, username: null });
    vi.mocked(adminLogin).mockResolvedValue({ authenticated: true, username: "admin" });
    renderPage();
    await screen.findByRole("heading", { name: "Quản trị dữ liệu phân tử" });
    await userEvent.type(screen.getByLabelText("Tên đăng nhập"), "admin");
    await userEvent.type(screen.getByLabelText("Mật khẩu"), "admin@123");
    await userEvent.click(screen.getByRole("button", { name: "Đăng nhập" }));
    expect(await screen.findByRole("heading", { name: "Dữ liệu phân tử" })).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: /NH3/ })).toBeInTheDocument();
  });

  it("restores an existing session without showing the login form", async () => {
    vi.mocked(adminSession).mockResolvedValue({ authenticated: true, username: "admin" });
    renderPage();
    expect(await screen.findByRole("heading", { name: "Dữ liệu phân tử" })).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Quản trị dữ liệu phân tử" })).not.toBeInTheDocument();
  });

  it("searches molecules through the backend", async () => {
    vi.mocked(adminSession).mockResolvedValue({ authenticated: true, username: "admin" });
    renderPage();
    await screen.findByRole("button", { name: /NH3/ });
    await userEvent.type(screen.getByLabelText("Tìm kiếm"), "NH3");
    await waitFor(() => expect(listAdminMolecules).toHaveBeenLastCalledWith("NH3"));
  });

  it("selects a molecule, edits a field, validates, previews and saves it", async () => {
    vi.mocked(adminSession).mockResolvedValue({ authenticated: true, username: "admin" });
    vi.mocked(validateAdminMolecule).mockResolvedValue({ is_valid: true, errors: [], warnings: [], info: [] });
    vi.mocked(previewAdminMolecule).mockResolvedValue(waterAnalysis);
    vi.mocked(updateAdminMolecule).mockResolvedValue({
      molecule: nh3ListItem, validation: { is_valid: true, errors: [], warnings: [], info: [] }, saved_at: new Date().toISOString(),
    });

    renderPage();
    await userEvent.click(await screen.findByRole("button", { name: /NH3/ }));
    await screen.findByRole("heading", { name: "NH3" });

    await userEvent.click(screen.getByRole("tab", { name: "Nội dung giảng dạy" }));
    const generalNote = screen.getByLabelText("English", { selector: "#teaching-general-en" });
    await userEvent.type(generalNote, "Edited teaching note");
    expect(screen.getByText("Thay đổi chưa lưu")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Kiểm tra" }));
    await waitFor(() => expect(validateAdminMolecule).toHaveBeenCalled());
    expect(await screen.findByText("Hợp lệ")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Xem trước phân tích" }));
    await waitFor(() => expect(previewAdminMolecule).toHaveBeenCalled());
    expect(await screen.findByRole("heading", { name: "Xem trước phân tích" })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Lưu" }));
    await waitFor(() => expect(updateAdminMolecule).toHaveBeenCalledWith("nh3", expect.objectContaining({
      molecule: expect.objectContaining({ teaching_note_en: expect.stringContaining("Edited teaching note") }),
    })));
    expect(await screen.findByText("Đã lưu")).toBeInTheDocument();
  });

  it("logs out and returns to the login form", async () => {
    vi.mocked(adminSession).mockResolvedValue({ authenticated: true, username: "admin" });
    vi.mocked(adminLogout).mockResolvedValue({ authenticated: false, username: null });
    renderPage();
    await screen.findByRole("heading", { name: "Dữ liệu phân tử" });
    await userEvent.click(screen.getByRole("button", { name: "Đăng xuất" }));
    await waitFor(() => expect(adminLogout).toHaveBeenCalled());
    expect(await screen.findByRole("heading", { name: "Quản trị dữ liệu phân tử" })).toBeInTheDocument();
  });
});
