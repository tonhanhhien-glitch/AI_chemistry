import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ChemFormula, readChemFormula } from "../utils/chemFormula";

describe("ChemFormula", () => {
  it("renders a bare formula with no indices and no script stack", () => {
    const { container } = render(<ChemFormula text="CO" />);
    expect(container.textContent).toBe("CO");
    expect(container.querySelector(".chemical-script-stack")).toBeNull();
  });

  it("renders a trailing subscript with no charge inside the shared script-stack slot", () => {
    const { container } = render(<ChemFormula text="CO2" />);
    const stack = container.querySelector(".chemical-script-stack");
    expect(stack).not.toBeNull();
    expect(stack?.querySelector(".chemical-subscript")?.textContent).toBe("2");
    expect(stack?.querySelector(".chemical-superscript")).toBeNull();
    expect(container.textContent).toBe("CO2");
  });

  it("renders a bare charge with no subscript inside the shared script-stack slot", () => {
    const { container } = render(<ChemFormula text="Na+" />);
    const stack = container.querySelector(".chemical-script-stack");
    expect(stack).not.toBeNull();
    expect(stack?.querySelector(".chemical-superscript")?.textContent).toBe("+");
    expect(stack?.querySelector(".chemical-subscript")).toBeNull();
  });

  it("renders a negative bare charge using the unicode minus sign", () => {
    const { container } = render(<ChemFormula text="Cl-" />);
    expect(container.querySelector(".chemical-superscript")?.textContent).toBe("−");
  });

  it("stacks a trailing subscript and charge in the same grid cell instead of two sequential elements", () => {
    const { container } = render(<ChemFormula text="CO3^2-" />);
    const stack = container.querySelector(".chemical-script-stack");
    expect(stack).not.toBeNull();
    expect(stack?.querySelector(".chemical-subscript")?.textContent).toBe("3");
    expect(stack?.querySelector(".chemical-superscript")?.textContent).toBe("2−");
    expect(container.textContent).toBe("CO2−3");
    // both scripts sit in one stack element, not in two separately-positioned siblings
    expect(container.querySelectorAll(".chemical-script-stack").length).toBe(1);
  });

  it.each([
    ["CO3^2-", "CO", "3", "2−"],
    ["SO4^2-", "SO", "4", "2−"],
    ["PO4^3-", "PO", "4", "3−"],
    ["NH4+", "NH", "4", "+"],
    ["NO3-", "NO", "3", "−"],
  ])("stacks the subscript and charge for %s", (input, prefix, subscript, charge) => {
    const { container } = render(<ChemFormula text={input} />);
    expect(container.textContent).toBe(`${prefix}${charge}${subscript}`);
    const stack = container.querySelector(".chemical-script-stack");
    expect(stack?.querySelector(".chemical-subscript")?.textContent).toBe(subscript);
    expect(stack?.querySelector(".chemical-superscript")?.textContent).toBe(charge);
  });

  it("gives an interior subscript (H3O+) its own script stack too, distinct from the trailing charge stack", () => {
    const { container } = render(<ChemFormula text="H3O+" />);
    const stacks = container.querySelectorAll(".chemical-script-stack");
    expect(stacks.length).toBe(2);
    expect(stacks[0].querySelector(".chemical-subscript")?.textContent).toBe("3");
    expect(stacks[0].querySelector(".chemical-superscript")).toBeNull();
    expect(stacks[1].querySelector(".chemical-superscript")?.textContent).toBe("+");
    expect(stacks[1].querySelector(".chemical-subscript")).toBeNull();
    expect(container.textContent).toBe("H3O+");
  });

  it("does not break earlier atom-count subscripts in longer formulas (H2SO4), each getting its own stack", () => {
    const { container } = render(<ChemFormula text="H2SO4" />);
    const stacks = container.querySelectorAll(".chemical-script-stack");
    expect(stacks.length).toBe(2);
    expect(stacks[0].querySelector(".chemical-subscript")?.textContent).toBe("2");
    expect(stacks[1].querySelector(".chemical-subscript")?.textContent).toBe("4");
    expect(container.textContent).toBe("H2SO4");
  });

  it("stacks a middle subscript with no trailing charge (H2O)", () => {
    const { container } = render(<ChemFormula text="H2O" />);
    const stacks = container.querySelectorAll(".chemical-script-stack");
    expect(stacks.length).toBe(1);
    expect(stacks[0].querySelector(".chemical-subscript")?.textContent).toBe("2");
    expect(stacks[0].querySelector(".chemical-superscript")).toBeNull();
    expect(container.textContent).toBe("H2O");
  });

  it("uses the identical subscript slot for a middle subscript (H2O) and a trailing one (CO2)", () => {
    const middle = render(<ChemFormula text="H2O" />);
    const trailing = render(<ChemFormula text="CO2" />);
    const a = middle.container.querySelector(".chemical-script-stack .chemical-subscript");
    const b = trailing.container.querySelector(".chemical-script-stack .chemical-subscript");
    expect(a?.tagName).toBe(b?.tagName);
    expect(a?.className).toBe(b?.className);
    expect(a?.parentElement?.className).toBe(b?.parentElement?.className);
  });

  it("does not show a bare magnitude-1 charge as 1+/1-", () => {
    const { container } = render(<ChemFormula text="NH4+" />);
    expect(container.textContent).not.toContain("1+");
    const { container: container2 } = render(<ChemFormula text="NO3-" />);
    expect(container2.textContent).not.toContain("1−");
  });

  it("shows the charge magnitude when greater than 1", () => {
    const { container } = render(<ChemFormula text="CO3^2-" />);
    expect(container.querySelector(".chemical-superscript")?.textContent).toBe("2−");
  });

  // Regression guard for the bug where the subscript/charge were placed in two
  // separate grid rows: an empty row let the browser reposition the remaining
  // script. With a single shared grid cell, the DOM shape (class + grid cell)
  // of a lone subscript or lone charge is identical whether or not the other
  // script is present, so their layout can never depend on each other.
  it("uses the identical script-stack slot for a subscript whether or not a charge is present", () => {
    const soleSubscript = render(<ChemFormula text="CO2" />);
    const stackedSubscript = render(<ChemFormula text="CO3^2-" />);
    const a = soleSubscript.container.querySelector(".chemical-script-stack .chemical-subscript");
    const b = stackedSubscript.container.querySelector(".chemical-script-stack .chemical-subscript");
    expect(a?.tagName).toBe(b?.tagName);
    expect(a?.className).toBe(b?.className);
  });

  it("uses the identical script-stack slot for a charge whether or not a subscript is present", () => {
    const soleCharge = render(<ChemFormula text="Cl-" />);
    const stackedCharge = render(<ChemFormula text="CO3^2-" />);
    const a = soleCharge.container.querySelector(".chemical-script-stack .chemical-superscript");
    const b = stackedCharge.container.querySelector(".chemical-script-stack .chemical-superscript");
    expect(a?.tagName).toBe(b?.tagName);
    expect(a?.className).toBe(b?.className);
  });

  it("exposes a readable plain-text label for accessibility", () => {
    expect(readChemFormula("CO3^2-")).toBe("CO3 2−");
    expect(readChemFormula("NH4+")).toBe("NH4 +");
    expect(readChemFormula("CO2")).toBe("CO2");
  });

  it("carries the accessible label on the wrapping element", () => {
    const { container } = render(<ChemFormula text="CO3^2-" />);
    expect(container.querySelector(".chemical-formula")?.getAttribute("aria-label")).toBe("CO3 2−");
  });
});
