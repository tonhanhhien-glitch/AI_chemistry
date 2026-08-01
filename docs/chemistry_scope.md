# Chemistry scope

## Supported contract

Curated teaching data covers main-group molecules and ions with reviewed connectivity and a defensible Lewis/VSEPR treatment. Steric number is 2–6 and the supported table is AX2, AX3, AX2E, AX4, AX3E, AX2E2, AX5, AX4E, AX3E2, AX2E3, AX6, AX5E, and AX4E2.

Curated records are CO2, BF3, SO2, H2O, NH3, CH4, NH4+, PCl5, SF4, ClF3, XeF2, SF6, BrF5, XeF4, NO3-, and CO3^2-. They continue to work offline. Curated Lewis/VSEPR facts always override external reference data.

For an uncurated validated PubChem identity—or a formula whose inventory has exactly one supported single-center form—automatic chemistry is deliberately narrower: one central main-group atom, one covalent unit, terminal H/halogen single bonds, a closed-shell electron count, a star connectivity graph when SMILES is available, and at most six electron domains. NF3 is supported by this general rule; it is not a special-case record.

## Refusal and ambiguity

The parser accepts canonical flat formulas and charge suffixes `+`, `-`, `^n+`, or `^n-`. Parsing is not identity resolution. Parentheses, hydrates/dot notation, isotopes, coefficients, transition-metal complexes, clusters, organometallics, multicentre bonds, arbitrary delocalized systems, steric number above six, and non-unique Lewis/connectivity results are refused unless explicitly curated.

PubChem formula hits are not accepted by position. Formula, charge, atom inventory, supported elements, covalent-unit count when present, and deterministic scope must all match. Multiple remaining candidates return `AMBIGUOUS_MOLECULE` with typed CID/name/formula/charge/SMILES provenance. Network degradation is typed and no raw exception reaches the browser.

## Three different electron pictures

- Lewis dots are a 2D valence-electron bookkeeping representation. Tests enforce total electron conservation, formal-charge sum, resonance notes, and lone-pair counts.
- VSEPR electron domains are pedagogical regions used to predict geometry. The 3D lone-pair lobes are illustrative and are not additional chemical atoms.
- Quantum electron density is a calculated physical field. This application does not claim its translucent lobes are orbitals, literal electron paths, or quantum electron-density surfaces.

## Three different angle concepts

- The rendered-coordinate angle is calculated by vector dot product from the active 3D model and is the only value drawn on its arc.
- An ideal VSEPR angle belongs to an idealized electron-domain template.
- A teaching/reference angle may be approximate, a range, or an inequality (for example NH3 about 107° or H2O about 104.5°).

These values may differ and the UI labels their sources separately.

## Review status

Curated records retain their existing review status. PubChem identity validation and deterministic consistency tests do not equal expert review. Uncurated results are labeled accordingly, and computational conformers are never labeled experimental without explicit evidence.
