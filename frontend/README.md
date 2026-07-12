# Frontend Task Checklist

## Setup

- [ ] Create `frontend/` folder.
- [ ] Initialize Vite React project.
- [ ] Enable TypeScript.
- [ ] Install Axios.
- [ ] Install 3Dmol.js.
- [ ] Install styling framework.
- [ ] Create routing.
- [ ] Create environment config.
- [ ] Add frontend Dockerfile.
- [ ] Configure API base URL.

## Layout (`src/components/layout/`)

- [ ] Create Header.
- [ ] Create Footer.
- [ ] Create PageContainer.
- [ ] Create responsive layout.
- [ ] Add UI labels.
- [ ] Add mobile-friendly design.
- [ ] Add loading states.
- [ ] Add error states.

## Home Page (`src/pages/HomePage.tsx`)

- [ ] Add project title.
- [ ] Add short description.
- [ ] Add formula/name input box.
- [ ] Add example molecule cards.
- [ ] Add supported-scope notice.
- [ ] Add quick-start guide.
- [ ] Link to examples page.
- [ ] Link to VSEPR rules page.

## Formula Input (`src/components/input/FormulaInput.tsx`)

- [ ] Support formulas like `H2O`, `NH3`, `CO2`.
- [ ] Support ions like `NH4+`, `SO4^2-`, `NO3-`.
- [ ] Validate empty input.
- [ ] Show malformed formula warning.
- [ ] Submit to backend `/analyze`.
- [ ] Show loading indicator.

## Learning Pipeline UI (`src/components/workflow/`)

- [ ] Add steps: input, Lewis structure, AXnEm notation, electron geometry, molecular geometry, 3D model, AI explanation.
- [ ] Highlight current step.
- [ ] Allow step navigation.
- [ ] Collapse sections on mobile.
- [ ] Keep full pipeline visible on desktop.

## Lewis Viewer (`src/components/lewis/LewisViewer.tsx`)

- [ ] Render atoms.
- [ ] Render bonds.
- [ ] Render lone pairs.
- [ ] Render formal charges.
- [ ] Render resonance note.
- [ ] Render total valence electrons.
- [ ] Render central atom note.
- [ ] Add fallback if Lewis structure is unavailable.

## VSEPR Cards (`src/components/vsepr/VSEPRCard.tsx`)

- [ ] Show AXnEm notation.
- [ ] Show number of bonding domains.
- [ ] Show number of lone-pair domains.
- [ ] Show electron geometry.
- [ ] Show molecular geometry.
- [ ] Show ideal bond angle.
- [ ] Show distortion note.
- [ ] Add geometry icon.
- [ ] Add short teaching explanation.

## 3Dmol.js Viewer (`src/components/viewer3d/Molecule3DViewer.tsx`)

- [ ] Load MolBlock/SDF/PDB data from backend.
- [ ] Render molecule using 3Dmol.js.
- [ ] Add rotate support.
- [ ] Add zoom support.
- [ ] Add reset view button.
- [ ] Add fullscreen button.
- [ ] Add ball-and-stick style.
- [ ] Add space-filling style.
- [ ] Add atom labels toggle.
- [ ] Add bond labels optional.
- [ ] Add fallback for failed rendering.
- [ ] Add mobile touch support.

## AI Explanation Panel (`src/components/explanation/ExplanationPanel.tsx`)

- [ ] Display  explanation.
- [ ] Add explanation level selector.
- [ ] Add sections: Lewis structure, AXnEm notation, electron geometry, molecular geometry, structure-property relationship, learning note.
- [ ] Add AI disclaimer.
- [ ] Add regenerate explanation button.
- [ ] Add copy explanation button.

## Property Table (`src/components/properties/PropertyTable.tsx`)

- [ ] Display molecular formula.
- [ ] Display charge.
- [ ] Display molecular mass.
- [ ] Display PubChem CID.
- [ ] Display SMILES.
- [ ] Display common name.
- [ ] Display polarity note if available.
- [ ] Separate verified teaching data from external reference data.

## Examples Page (`src/pages/ExamplesPage.tsx`)

- [ ] Group examples by geometry.
- [ ] Add linear examples.
- [ ] Add trigonal planar examples.
- [ ] Add bent examples.
- [ ] Add tetrahedral examples.
- [ ] Add trigonal pyramidal examples.
- [ ] Add trigonal bipyramidal examples.
- [ ] Add octahedral examples.
- [ ] Let user click example to run analysis.

## VSEPR Rules Page (`src/pages/RulesPage.tsx`)

- [ ] Display VSEPR rule table.
- [ ] Show AXnEm notation.
- [ ] Show electron geometry.
- [ ] Show molecular geometry.
- [ ] Show bond angle.
- [ ] Show example molecule.
- [ ] Add simple diagrams or icons.
- [ ] Add  teaching notes.

## Feedback UI (`src/components/feedback/FeedbackForm.tsx`)

- [ ] Add rating for clarity.
- [ ] Add rating for usefulness.
- [ ] Add rating for 3D model usefulness.
- [ ] Add chemistry error report field.
- [ ] Add general comment field.
- [ ] Submit to backend `/feedback`.

## Survey and Evaluation UI (`src/components/survey/`, `src/pages/SurveyPage.tsx`)

- [ ] Create pre-test module.
- [ ] Create post-test module.
- [ ] Create Likert survey form.
- [ ] Store anonymous student ID or session ID.
- [ ] Submit survey result to backend.
- [ ] Add CSV export for teacher/researcher.
- [ ] Add basic result summary page.

## Integration

- [ ] Define shared TypeScript types matching backend Pydantic schemas.
- [ ] Implement API client (`src/api/client.ts`).
- [ ] Connect formula input to `/api/v1/analyze`.
- [ ] Render backend errors.
- [ ] Render Lewis output.
- [ ] Render VSEPR output.
- [ ] Render 3D model.
- [ ] Render AI explanation.
- [ ] Render property table.
- [ ] Add loading state.
- [ ] Add retry button.
