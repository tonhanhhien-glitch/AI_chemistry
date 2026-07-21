# Chemistry scope

## Supported contract

Production teaching data is limited to main-group molecules and ions with curated connectivity and a defensible Lewis/VSEPR treatment. Steric number is 2–6. Supported classes are AX2, AX3, AX2E, AX4, AX3E, AX2E2, AX5, AX4E, AX3E2, AX2E3, AX6, AX5E, and AX4E2.

Curated records are CO2, BF3, SO2, H2O, NH3, CH4, NH4+, PCl5, SF4, ClF3, XeF2, SF6, BrF5, XeF4, NO3-, and CO3^2-. Nitrate and carbonate have three equivalent curated resonance forms; SO2 has a resonance note. BF3 is electron-deficient and appropriate period-3-or-later records are marked expanded-octet.

The parser accepts canonical flat formulas and charge suffixes +, -, or ^n+/^n-. Repeated symbols accumulate, so CH3COOH parses to C2H4O2, but parsing is not identity resolution.

## Exclusions

- Parentheses, hydrates/dot notation, isotopes, coefficients, leading-zero counts.
- Transition-metal complexes, clusters, organometallics, and steric number above 6.
- Arbitrary Lewis generation from composition alone.
- Formula-to-connectivity guessing when constitutional isomers exist.
- Quantum-optimized geometry claims.

Unsupported syntax returns UNSUPPORTED_FORMULA_SYNTAX; unsupported elements return UNSUPPORTED_ELEMENT; a parsed formula without curated connectivity returns UNSUPPORTED_MOLECULE; multiple identities return AMBIGUOUS_MOLECULE with candidates.

## Central atom and labels

Curated override wins. The fallback heuristic excludes only H and F, then prefers a unique least-electronegative candidate. Cl, Br, I, and Xe remain eligible. The heuristic never establishes connectivity.

Hybridization labels for steric numbers 2–6 are optional pedagogical VSEPR-era approximations, not a complete modern orbital description.

## Review status

All records are internal_golden_pending_expert_signoff. Automated tests establish consistency, not external approval. Review must cover Lewis/formal charge, resonance/exception notes, domain counts, geometry/angle language, polarity, Vietnamese terminology, and future external identifiers/properties.
