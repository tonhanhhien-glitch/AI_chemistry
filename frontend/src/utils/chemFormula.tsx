// Renders chemical formulas and AXE notation (e.g. "CO2", "NO3-", "AX2E1")
// with proper subscript atom counts and superscript ionic charges.
import type { ReactNode } from "react";

// Explicit magnitude, e.g. "CO3^2-" -> charge "2-". The caret is what marks
// the following digit as part of the charge rather than an atom subscript.
const CARET_CHARGE = /\^(\d*)([+-])$/;
// Bare trailing sign, e.g. "NO3-" or "NH4+" -> charge magnitude 1. Any digit
// just before the sign is an atom subscript (the "3" in NO3), not a charge count.
const PLAIN_CHARGE = /([+-])$/;

function parseChemFormula(text: string): { base: string; charge: string } {
  const caretMatch = text.match(CARET_CHARGE);
  const plainMatch = caretMatch ? null : text.match(PLAIN_CHARGE);
  const chargeMatch = caretMatch ?? plainMatch;
  if (!chargeMatch || chargeMatch.index === undefined) return { base: text, charge: "" };
  const base = text.slice(0, chargeMatch.index);
  const count = caretMatch ? caretMatch[1] : "";
  const sign = chargeMatch[chargeMatch.length - 1];
  return { base, charge: `${count}${sign === "-" ? "−" : "+"}` };
}

// Plain-text reading for aria-label / accessibility, e.g. "CO3^2-" -> "CO3 2−".
export function readChemFormula(text: string): string {
  if (!text) return text;
  const { base, charge } = parseChemFormula(text);
  return charge ? `${base} ${charge}` : base;
}

export function formatChemFormula(text: string): ReactNode[] {
  if (!text) return [text];
  const { base, charge } = parseChemFormula(text);

  const segments = base.split(/(\d+)/).filter(Boolean);
  const lastSegment = segments[segments.length - 1];
  const lastIsSubscript = lastSegment !== undefined && /^\d+$/.test(lastSegment);

  // The final atom-count subscript and the ionic charge (if any) both attach to
  // the same trailing character, so they share one script-stack slot. Interior
  // subscripts (e.g. the "2" in H2O or H2SO4) get their own single-script stack
  // too, rather than a plain inline <sub> — same grid-cell mechanism, same
  // sizing/offset, just without a superscript to pair with. That keeps every
  // atom-count subscript in a formula visually consistent, whether or not it
  // happens to sit next to a charge.
  const finalSubscript = lastIsSubscript ? lastSegment : null;
  const bodySegments = finalSubscript !== null ? segments.slice(0, -1) : segments;

  const parts: ReactNode[] = bodySegments.map((segment, index) =>
    /^\d+$/.test(segment) ? (
      <span className="chemical-script-stack" key={`sub-${index}`}>
        <sub className="chemical-subscript">{segment}</sub>
      </span>
    ) : (
      segment
    ),
  );

  if (finalSubscript !== null || charge) {
    parts.push(
      <span className="chemical-script-stack" key="stack">
        {charge && <sup className="chemical-superscript">{charge}</sup>}
        {finalSubscript !== null && <sub className="chemical-subscript">{finalSubscript}</sub>}
      </span>,
    );
  }

  return parts;
}

export function ChemFormula({ text, className }: { text: string; className?: string }) {
  return (
    <span className={className ? `chemical-formula ${className}` : "chemical-formula"} aria-label={readChemFormula(text)}>
      {formatChemFormula(text)}
    </span>
  );
}
