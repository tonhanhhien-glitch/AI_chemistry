import { useState } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import FormulaInput from "../components/input/FormulaInput";
import { I18nProvider, useI18n } from "../i18n";
import * as moleculeApi from "../api/moleculeApi";
import type { MoleculeSummary } from "../types/molecule";

const mockResults: MoleculeSummary[] = [
  {
    id: "nh3",
    formula: "NH3",
    name_en: "Ammonia",
    name_vi: "Amoniac",
    ax_en: "AX3E",
    molecular_geometry: "trigonal pyramidal",
    molecular_geometry_vi: "chóp tam giác",
    review_status: "approved",
  },
  {
    id: "h2o",
    formula: "H2O",
    name_en: "Water",
    name_vi: "Nước",
    ax_en: "AX2E2",
    molecular_geometry: "bent",
    molecular_geometry_vi: "gấp khúc",
    review_status: "approved",
  },
];

function InputWithI18n({
  initialLang = "en",
  onSelect,
  onSubmit,
}: {
  initialLang?: string;
  onSelect?: (item: MoleculeSummary) => void;
  onSubmit?: (item?: MoleculeSummary) => void;
}) {
  window.localStorage.setItem("vsepr-lang", initialLang);
  return (
    <I18nProvider>
      <InputConsumer onSelect={onSelect} onSubmit={onSubmit} />
    </I18nProvider>
  );
}

function InputConsumer({
  onSelect,
  onSubmit,
}: {
  onSelect?: (item: MoleculeSummary) => void;
  onSubmit?: (item?: MoleculeSummary) => void;
}) {
  const { lang, setLang } = useI18n();
  const [value, setValue] = useState("");

  return (
    <div>
      <button type="button" data-testid="toggle-lang" onClick={() => setLang(lang === "vi" ? "en" : "vi")}>
        Toggle Lang
      </button>
      <FormulaInput
        value={value}
        onChange={setValue}
        onSubmit={onSubmit ?? (() => {})}
        onSelectMolecule={onSelect}
      />
    </div>
  );
}

describe("FormulaInput Autocomplete i18n", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.localStorage.clear();
  });

  it("renders autocomplete geometry and placeholder in English", async () => {
    vi.spyOn(moleculeApi, "searchMolecules").mockResolvedValue(mockResults);
    const user = userEvent.setup();

    render(<InputWithI18n initialLang="en" />);

    const input = screen.getByLabelText(/Formula or substance name/i);
    expect(input).toBeInTheDocument();
    expect(screen.getByPlaceholderText("e.g. H2O, XeF4, NO3-")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Analyze" })).toBeInTheDocument();

    await user.type(input, "nh3");

    expect(await screen.findByText(/trigonal pyramidal/i)).toBeInTheDocument();
    expect(screen.getByText("Ammonia")).toBeInTheDocument();
    expect(screen.queryByText("chóp tam giác")).not.toBeInTheDocument();
    expect(screen.queryByText("Amoniac")).not.toBeInTheDocument();
  });

  it("renders autocomplete geometry and placeholder in Vietnamese", async () => {
    vi.spyOn(moleculeApi, "searchMolecules").mockResolvedValue(mockResults);
    const user = userEvent.setup();

    render(<InputWithI18n initialLang="vi" />);

    const input = screen.getByLabelText(/Công thức hoặc tên chất/i);
    expect(input).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Ví dụ: H2O, XeF4, NO3-")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Tìm" })).toBeInTheDocument();

    await user.type(input, "nh3");

    expect(await screen.findByText(/chóp tam giác/i)).toBeInTheDocument();
    expect(screen.getByText("Amoniac")).toBeInTheDocument();
    expect(screen.queryByText("trigonal pyramidal")).not.toBeInTheDocument();
  });

  it("updates open autocomplete suggestion labels immediately when language changes without refetching", async () => {
    const searchSpy = vi.spyOn(moleculeApi, "searchMolecules").mockResolvedValue(mockResults);
    const user = userEvent.setup();

    render(<InputWithI18n initialLang="vi" />);

    const input = screen.getByLabelText(/Công thức hoặc tên chất/i);
    await user.type(input, "nh3");

    // Vietnamese labels visible
    expect(await screen.findByText(/chóp tam giác/i)).toBeInTheDocument();
    expect(screen.getByText("Amoniac")).toBeInTheDocument();
    expect(searchSpy).toHaveBeenCalledTimes(1);

    // Switch to English and focus input again
    await user.click(screen.getByTestId("toggle-lang"));
    await user.click(input);

    // Dropdown updates immediately to English
    expect(await screen.findByText(/trigonal pyramidal/i)).toBeInTheDocument();
    expect(screen.getByText("Ammonia")).toBeInTheDocument();
    expect(screen.queryByText("chóp tam giác")).not.toBeInTheDocument();
    expect(screen.queryByText("Amoniac")).not.toBeInTheDocument();

    // No extra search API calls should have been made
    expect(searchSpy).toHaveBeenCalledTimes(1);
  });

  it("selects a suggestion using click and keyboard", async () => {
    vi.spyOn(moleculeApi, "searchMolecules").mockResolvedValue(mockResults);
    const onSelect = vi.fn();
    const user = userEvent.setup();

    render(<InputWithI18n initialLang="en" onSelect={onSelect} />);

    const input = screen.getByLabelText(/Formula or substance name/i);
    await user.type(input, "nh3");

    const option = await screen.findByText("Ammonia");
    await user.click(option);

    expect(onSelect).toHaveBeenCalledWith(mockResults[0]);
  });
});
