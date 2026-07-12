# Backend Task Checklist

## Setup

- [x] Create `backend/` folder.
- [ ] Initialize Python environment.
- [x] Install FastAPI.
- [x] Install Uvicorn.
- [x] Install Pydantic.
- [ ] Install RDKit.
- [ ] Install PubChemPy.
- [ ] Install Anthropic SDK.
- [ ] Install python-dotenv.
- [x] Install pytest.
- [x] Create `app/main.py`.
- [x] Create `/api/v1/health` endpoint.
- [x] Configure CORS for frontend.
- [x] Create `.env.example`.
- [x] Add Dockerfile for backend.

## Chemistry Scope Definition

- [ ] Define supported molecules and ions.
- [ ] Limit scope to main-group inorganic molecules and ions.
- [ ] Limit VSEPR cases to `n + m <= 6`.
- [ ] Exclude transition-metal complexes.
- [ ] Exclude clusters.
- [ ] Exclude molecules outside simple Lewis/VSEPR treatment.
- [ ] Create `docs/chemistry_scope.md`.
- [ ] Create expert-review checklist for supported examples.

## Data Files

- [ ] Populate `element_valence.json`.
- [ ] Populate `vsepr_rules.json`.
- [ ] Populate `curated_molecules.json`.
- [ ] Populate `lewis_templates.json`.
- [ ] Populate `geometry_templates_3d.json`.
- [ ] Populate `teaching_notes.json`.
- [ ] Populate `molecule_examples.json`.

## Formula Parser (`app/services/formula_parser.py`)

- [x] Parse neutral formulas: `H2O`, `NH3`, `CO2`.
- [x] Parse charged ions: `NH4+`, `SO4^2-`, `NO3-`.
- [x] Normalize formulas.
- [x] Extract element symbols.
- [x] Extract atom counts.
- [x] Extract formal charge.
- [x] Reject malformed formulas.
- [x] Reject unsupported elements.
- [x] Return user-friendly error messages.
- [x] Write parser unit tests.

## Molecule Resolver (`app/services/molecule_resolver.py`)

- [ ] Search molecule in curated database first.
- [ ] Search molecule using PubChemPy second.
- [ ] Use RDKit fallback if possible.
- [ ] Use manual VSEPR template fallback if RDKit/PubChem fails.
- [ ] Cache PubChem results.
- [ ] Return molecule name, formula, SMILES, PubChem CID, and basic properties.
- [ ] Write resolver unit tests.

## Lewis Structure Module (`app/services/lewis_service.py`, `app/chemistry/`)

- [ ] Calculate total valence electrons.
- [ ] Select likely central atom.
- [ ] Generate skeleton structure.
- [ ] Assign single bonds.
- [ ] Assign multiple bonds if needed.
- [ ] Assign lone pairs.
- [ ] Calculate formal charges.
- [ ] Detect resonance cases.
- [ ] Detect expanded octet cases.
- [ ] Detect electron-deficient cases.
- [ ] Detect odd-electron cases.
- [ ] Use curated Lewis templates when available.
- [ ] Return frontend-ready Lewis data.
- [ ] Write tests for common molecules and ions.

## VSEPR Engine (`app/services/vsepr_engine.py`, `app/chemistry/vsepr_rules.py`)

- [ ] Count bonding domains.
- [ ] Count lone-pair domains.
- [ ] Treat multiple bonds as one electron domain.
- [ ] Calculate total domains: `n + m`.
- [ ] Generate AXnEm notation.
- [ ] Map AXnEm to electron geometry.
- [ ] Map AXnEm to molecular geometry.
- [ ] Return ideal bond angle.
- [ ] Return distortion notes.
- [ ] Return teaching notes.
- [ ] Add support for AX2, AX3, AX2E, AX4, AX3E, AX2E2, AX5, AX4E, AX3E2, AX2E3, AX6, AX5E, AX4E2.
- [ ] Write unit tests:
  - [ ] CO2 -> AX2 -> linear
  - [ ] SO2 -> AX2E -> bent
  - [ ] H2O -> AX2E2 -> bent
  - [ ] NH3 -> AX3E -> trigonal pyramidal
  - [ ] CH4 -> AX4 -> tetrahedral
  - [ ] PCl5 -> AX5 -> trigonal bipyramidal
  - [ ] SF6 -> AX6 -> octahedral
  - [ ] XeF4 -> AX4E2 -> square planar

## 3D Structure Service (`app/services/structure3d_service.py`)

- [ ] Generate 3D structure using RDKit when SMILES is available.
- [ ] Retrieve PubChem 3D structure if available.
- [ ] Use VSEPR geometry template if automatic 3D generation fails.
- [ ] Export MolBlock/SDF/PDB-compatible data.
- [ ] Return atom coordinates.
- [ ] Return bond data.
- [ ] Return rendering metadata for 3Dmol.js.
- [ ] Add warning for illustrative 3D models.
- [ ] Cache generated 3D structures.
- [ ] Write tests for 3D generation.

## AI Explanation Service (`app/services/ai_explanation_service.py`, `app/prompts/`)

- [ ] Create prompt templates.
- [ ] Add explanation levels: Basic, Intermediate, Advanced.
- [ ] Send only verified backend facts to Claude API.
- [ ] Prevent AI from changing chemistry conclusions.
- [ ] Generate English/Vietnamese explanation.
- [ ] Explain Lewis structure.
- [ ] Explain AXnEm notation.
- [ ] Explain electron geometry.
- [ ] Explain molecular geometry.
- [ ] Explain relation between structure and properties.
- [ ] Add learning tips.
- [ ] Add contradiction-check step (`app/services/validation_service.py`).
- [ ] Cache AI explanations.
- [ ] Write tests for prompt generation.
- [ ] Write tests for contradiction detection.

## API Endpoints (`app/api/v1/`)

- [x] `GET /api/v1/health` — return backend status and version number.
- [x] `GET /api/v1/formula?formula=` — parse a strict flat formula.
- [ ] `GET /api/v1/molecules/examples` — return curated example molecules.
- [ ] `GET /api/v1/molecules/search?q=` — search by formula or name, return possible matches.
- [ ] `POST /api/v1/analyze` — parse, resolve, Lewis, VSEPR, 3D, properties, optional AI explanation.
- [ ] `POST /api/v1/explain` — generate explanation by level from a validated analysis result.
- [ ] `GET /api/v1/rules/vsepr` — return VSEPR rule table.
- [ ] `GET /api/v1/rules/examples` — return examples by geometry type.
- [ ] `POST /api/v1/feedback` — save user feedback and chemistry error reports.
- [ ] `POST /api/v1/survey` — save Likert/pre-test/post-test results; export CSV.

## Testing (`tests/`)

- [x] Test formula parser.
- [ ] Test molecule resolver.
- [ ] Test PubChem connection.
- [ ] Test RDKit generation.
- [ ] Test Lewis output.
- [ ] Test VSEPR output.
- [ ] Test AI prompt.
- [x] Test API response schema.
- [ ] Test full pipeline.
- [ ] Build golden molecule test set.
- [ ] Ask chemistry expert to validate golden set.
