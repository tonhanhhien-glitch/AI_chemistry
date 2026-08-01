# Frontend

The authoritative UI is the React + TypeScript + Vite application in this directory. `Molecule3DViewer` loads native SDF as `sdf`, MolBlock as `mol`, PDB as `pdb`, and constructs XYZ only for coordinate responses. It provides stick, ball-and-stick, and space-filling representations; atom labels; coordinate-derived angle arcs; illustrative lone-pair domains; reset; fullscreen; provenance badges; warnings; and WebGL fallback. Ambiguous PubChem formulas show validated candidates and resubmit the unchanged formula with `pubchem_cid`.

## Run and verify

```bash
npm ci
npm test
npm run lint
npm run build
npm run dev
```

Manual NF3 verification with a PubChem-enabled backend:

1. Open `http://localhost:5173/analysis`, enter `NF3`, and confirm Lewis shows 26 electrons, AX3E, one central lone pair, and trigonal-pyramidal geometry.
2. Confirm the source badge reports PubChem 3D, RDKit-generated conformer, or Idealized VSEPR model according to the configured fallback.
3. Enable **Bond angle**. Confirm two rays, an arc, and a coordinate-derived label appear; compare it with the separately labeled VSEPR reference angle.
4. Enable **Lone-pair domains**. Confirm a translucent two-sphere domain appears outside N and the explanatory text says it is illustrative.
5. Disable each toggle to confirm only its own shapes disappear; enable atom labels to confirm angle changes do not remove them.

# Frontend Task Checklist

## Setup

- [x] Create `frontend/` folder.
- [x] Initialize Vite React project.
- [x] Enable TypeScript.
- [x] Install Axios.
- [x] Install 3Dmol.js.
- [ ] Install styling framework.
- [x] Create routing.
- [x] Create environment config.
- [x] Add frontend Dockerfile.
- [x] Configure API base URL.

## Layout (`src/components/layout/`)

- [x] Create Header.
- [x] Create Footer.
- [x] Create PageContainer.
- [x] Create responsive layout.
- [x] Add UI labels.
- [x] Add mobile-friendly design.
- [x] Add loading states.
- [x] Add error states.

## Home Page (`src/pages/HomePage.tsx`)

- [x] Add project title.
- [x] Add short description.
- [x] Add formula/name input box.
- [x] Add example molecule cards.
- [x] Add supported-scope notice.
- [x] Add quick-start guide.
- [x] Link to examples page.
- [x] Link to VSEPR rules page.

## Formula Input (`src/components/input/FormulaInput.tsx`)

- [x] Support formulas like `H2O`, `NH3`, `CO2`.
- [x] Support ions like `NH4+`, `SO4^2-`, `NO3-`.
- [x] Validate empty input.
- [x] Show malformed formula warning.
- [x] Submit to backend `/analyze`.
- [x] Show loading indicator.

## Learning Pipeline UI (`src/components/workflow/`)

- [x] Add steps: input, Lewis structure, AXnEm notation, electron geometry, molecular geometry, 3D model, AI explanation.
- [ ] Highlight current step.
- [ ] Allow step navigation.
- [ ] Collapse sections on mobile.
- [x] Keep full pipeline visible on desktop.

## Lewis Viewer (`src/components/lewis/LewisViewer.tsx`)

- [x] Render atoms.
- [x] Render bonds.
- [x] Render lone pairs.
- [x] Render formal charges.
- [x] Render resonance note.
- [x] Render total valence electrons.
- [ ] Render central atom note.
- [ ] Add fallback if Lewis structure is unavailable.

## VSEPR Cards (`src/components/vsepr/VSEPRCard.tsx`)

- [x] Show AXnEm notation.
- [x] Show number of bonding domains.
- [x] Show number of lone-pair domains.
- [x] Show electron geometry.
- [x] Show molecular geometry.
- [x] Show ideal bond angle.
- [x] Show distortion note.
- [x] Add geometry icon.
- [x] Add short teaching explanation.

## 3Dmol.js Viewer (`src/components/viewer3d/Molecule3DViewer.tsx`)

- [x] Load MolBlock/SDF/PDB data from backend.
- [x] Render molecule using 3Dmol.js.
- [x] Add rotate support.
- [x] Add zoom support.
- [x] Add reset view button.
- [x] Add fullscreen button.
- [x] Add ball-and-stick style.
- [x] Add space-filling style.
- [x] Add atom labels toggle.
- [ ] Add bond labels optional.
- [x] Add fallback for failed rendering.
- [x] Add mobile touch support.

## AI Explanation Panel (`src/components/explanation/ExplanationPanel.tsx`)

- [x] Display  explanation.
- [x] Add explanation level selector.
- [x] Add sections: Lewis structure, AXnEm notation, electron geometry, molecular geometry, structure-property relationship, learning note.
- [x] Add AI disclaimer.
- [x] Add regenerate explanation button.
- [x] Add copy explanation button.

## Property Table (`src/components/properties/PropertyTable.tsx`)

- [ ] Display molecular formula.
- [ ] Display charge.
- [x] Display molecular mass.
- [ ] Display PubChem CID.
- [ ] Display SMILES.
- [ ] Display common name.
- [x] Display polarity note if available.
- [x] Separate verified teaching data from external reference data.

## Examples Page (`src/pages/ExamplesPage.tsx`)

- [x] Group examples by geometry.
- [x] Add linear examples.
- [x] Add trigonal planar examples.
- [x] Add bent examples.
- [x] Add tetrahedral examples.
- [x] Add trigonal pyramidal examples.
- [x] Add trigonal bipyramidal examples.
- [x] Add octahedral examples.
- [x] Let user click example to run analysis.

## VSEPR Rules Page (`src/pages/RulesPage.tsx`)

- [x] Display VSEPR rule table.
- [x] Show AXnEm notation.
- [x] Show electron geometry.
- [x] Show molecular geometry.
- [x] Show bond angle.
- [x] Show example molecule.
- [x] Add simple diagrams or icons.
- [x] Add  teaching notes.

## Feedback UI (`src/components/feedback/FeedbackForm.tsx`)

- [ ] Add rating for clarity.
- [ ] Add rating for usefulness.
- [ ] Add rating for 3D model usefulness.
- [x] Add chemistry error report field.
- [x] Add general comment field.
- [x] Submit to backend `/feedback`.

## Survey and Evaluation UI (`src/components/survey/`, `src/pages/SurveyPage.tsx`)

- [x] Create pre-test module.
- [x] Create post-test module.
- [x] Create Likert survey form.
- [x] Store anonymous student ID or session ID.
- [x] Submit survey result to backend.
- [ ] Add CSV export for teacher/researcher.
- [ ] Add basic result summary page.

## Integration

- [x] Define shared TypeScript types matching backend Pydantic schemas.
- [x] Implement API client (`src/api/client.ts`).
- [x] Connect formula input to `/api/v1/analyze`.
- [x] Render backend errors.
- [x] Render Lewis output.
- [x] Render VSEPR output.
- [x] Render 3D model.
- [x] Render AI explanation.
- [x] Render property table.
- [x] Add loading state.
- [x] Add retry button.
