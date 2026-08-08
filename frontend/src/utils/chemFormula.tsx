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

// Every element symbol, so a token that merely has the shape of a formula
// ("COVID19", "IT4") stays plain prose instead of sprouting scripts.
const ELEMENT_SYMBOLS = new Set(
  ("H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr "
    + "Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm "
    + "Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No "
    + "Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og").split(" "),
);

// AXE notation is not built from element symbols, so it needs its own check.
const AXE_NOTATION = /^AX\d*(?:E\d*)?$/;
// A formula-shaped run of capitalised symbols and counts, with an optional
// trailing charge, taken only where it stands alone as a word. The lookarounds
// keep "CO2" inside "CO2-based" or a Vietnamese word from being pulled apart,
// and let the charge be dropped when a letter follows the sign.
const FORMULA_TOKEN = /(?<![\p{L}\p{N}])(?:[A-Z][a-z]?\d*)+(?:\^\d*[+-]|[+-])?(?![\p{L}\p{N}])/gu;

function isChemFormula(token: string): boolean {
  const { base, charge } = parseChemFormula(token);
  // Nothing to raise or lower — leave words like "VSEPR" or "Lewis" untouched.
  if (!charge && !/\d/.test(base)) return false;
  if (AXE_NOTATION.test(base)) return true;
  const symbols = base.match(/[A-Z][a-z]?/g);
  return symbols !== null && symbols.every((symbol) => ELEMENT_SYMBOLS.has(symbol));
}

// Renders a sentence of prose, giving every formula inside it the same
// script-stack treatment a standalone <ChemFormula> gets, so a charge in
// running text sits directly above its atom-count subscript just like on the
// VSEPR rules page. Non-formula text is passed through verbatim.
export function formatChemText(text: string): ReactNode[] {
  if (!text) return [text];
  const parts: ReactNode[] = [];
  let cursor = 0;
  for (const match of text.matchAll(FORMULA_TOKEN)) {
    const token = match[0];
    if (match.index === undefined || !isChemFormula(token)) continue;
    if (match.index > cursor) parts.push(text.slice(cursor, match.index));
    parts.push(<ChemFormula key={`formula-${match.index}`} text={token} />);
    cursor = match.index + token.length;
  }
  if (cursor < text.length) parts.push(text.slice(cursor));
  return parts;
}

export function ChemFormula({ text, className }: { text: string; className?: string }) {
  return (
    <span className={className ? `chemical-formula ${className}` : "chemical-formula"} aria-label={readChemFormula(text)}>
      {formatChemFormula(text)}
    </span>
  );
}
