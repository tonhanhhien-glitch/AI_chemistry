# Backend Task Checklist

## Setup

- [x] Create `backend/` folder.
- [x] Initialize Python environment.
- [x] Install FastAPI.
- [x] Install Uvicorn.
- [x] Install Pydantic.
- [x] Install RDKit.
- [x] Install PubChemPy.
- [x] Install Anthropic SDK.
- [ ] Install python-dotenv.
- [x] Install pytest.
- [x] Create `app/main.py`.
- [x] Create `/api/v1/health` endpoint.
- [x] Configure CORS for frontend.
- [x] Create `.env.example`.
- [x] Add Dockerfile for backend.

## Chemistry Scope Definition

- [x] Define supported molecules and ions.
- [x] Limit scope to main-group inorganic molecules and ions.
- [x] Limit VSEPR cases to `n + m <= 6`.
- [x] Exclude transition-metal complexes.
- [x] Exclude clusters.
- [x] Exclude molecules outside simple Lewis/VSEPR treatment.
- [x] Create `docs/chemistry_scope.md`.
- [x] Create expert-review checklist for supported examples.

## Data Files

- [x] Populate `element_valence.json`.
- [x] Populate `vsepr_rules.json`.
- [x] Populate `curated_molecules.json`.
- [x] Populate `lewis_templates.json`.
- [x] Populate `geometry_templates_3d.json`.
- [x] Populate `teaching_notes.json`.
- [x] Populate `molecule_examples.json`.

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

- [x] Search molecule in curated database first.
- [ ] Search molecule using PubChemPy second.
- [ ] Use RDKit fallback if possible.
- [ ] Use manual VSEPR template fallback if RDKit/PubChem fails.
- [x] Cache PubChem results.
- [ ] Return molecule name, formula, SMILES, PubChem CID, and basic properties.
- [x] Write resolver unit tests.

## Lewis Structure Module (`app/services/lewis_service.py`, `app/chemistry/`)

- [x] Calculate total valence electrons.
- [x] Select likely central atom.
- [x] Generate skeleton structure.
- [x] Assign single bonds.
- [x] Assign multiple bonds if needed.
- [x] Assign lone pairs.
- [x] Calculate formal charges.
- [x] Detect resonance cases.
- [x] Detect expanded octet cases.
- [x] Detect electron-deficient cases.
- [x] Detect odd-electron cases.
- [x] Use curated Lewis templates when available.
- [x] Return frontend-ready Lewis data.
- [x] Write tests for common molecules and ions.

## VSEPR Engine (`app/services/vsepr_engine.py`, `app/chemistry/vsepr_rules.py`)

- [x] Count bonding domains.
- [x] Count lone-pair domains.
- [x] Treat multiple bonds as one electron domain.
- [x] Calculate total domains: `n + m`.
- [x] Generate AXnEm notation.
- [x] Map AXnEm to electron geometry.
- [x] Map AXnEm to molecular geometry.
- [x] Return ideal bond angle.
- [x] Return distortion notes.
- [x] Return teaching notes.
- [x] Add support for AX2, AX3, AX2E, AX4, AX3E, AX2E2, AX5, AX4E, AX3E2, AX2E3, AX6, AX5E, AX4E2.
- [x] Write unit tests:
  - [x] CO2 -> AX2 -> linear
  - [x] SO2 -> AX2E -> bent
  - [x] H2O -> AX2E2 -> bent
  - [x] NH3 -> AX3E -> trigonal pyramidal
  - [x] CH4 -> AX4 -> tetrahedral
  - [x] PCl5 -> AX5 -> trigonal bipyramidal
  - [x] SF6 -> AX6 -> octahedral
  - [x] XeF4 -> AX4E2 -> square planar

## 3D Structure Service (`app/services/structure3d_service.py`)

- [ ] Generate 3D structure using RDKit when SMILES is available.
- [ ] Retrieve PubChem 3D structure if available.
- [x] Use VSEPR geometry template if automatic 3D generation fails.
- [ ] Export MolBlock/SDF/PDB-compatible data.
- [x] Return atom coordinates.
- [x] Return bond data.
- [x] Return rendering metadata for 3Dmol.js.
- [x] Add warning for illustrative 3D models.
- [ ] Cache generated 3D structures.
- [x] Write tests for 3D generation.

## AI Explanation Service (`app/services/ai_explanation_service.py`, `app/prompts/`)

- [x] Create prompt templates.
- [x] Add explanation levels: Basic, Intermediate, Advanced.
- [x] Send only verified backend facts to Claude API.
- [x] Prevent AI from changing chemistry conclusions.
- [x] Generate English/Vietnamese explanation.
- [x] Explain Lewis structure.
- [x] Explain AXnEm notation.
- [x] Explain electron geometry.
- [x] Explain molecular geometry.
- [x] Explain relation between structure and properties.
- [x] Add learning tips.
- [x] Add contradiction-check step (`app/services/validation_service.py`).
- [x] Cache AI explanations.
- [ ] Write tests for prompt generation.
- [x] Write tests for contradiction detection.

## API Endpoints (`app/api/v1/`)

- [x] `GET /api/v1/health` — return backend status and version number.
- [x] `GET /api/v1/formula?formula=` — parse a strict flat formula.
- [x] `GET /api/v1/molecules/examples` — return curated example molecules.
- [x] `GET /api/v1/molecules/search?q=` — search by formula or name, return possible matches.
- [x] `POST /api/v1/analyze` — parse, resolve, Lewis, VSEPR, 3D, properties, optional AI explanation.
- [x] `POST /api/v1/explain` — generate explanation by level from a validated analysis result.
- [x] `GET /api/v1/rules/vsepr` — return VSEPR rule table.
- [x] `GET /api/v1/rules/examples` — return examples by geometry type.
- [x] `POST /api/v1/feedback` — save user feedback and chemistry error reports.
- [x] `POST /api/v1/survey` — save Likert/pre-test/post-test results; export CSV.

## Testing (`tests/`)

- [x] Test formula parser.
- [x] Test molecule resolver.
- [ ] Test PubChem connection.
- [ ] Test RDKit generation.
- [x] Test Lewis output.
- [x] Test VSEPR output.
- [ ] Test AI prompt.
- [x] Test API response schema.
- [x] Test full pipeline.
- [x] Build golden molecule test set.
- [ ] Ask chemistry expert to validate golden set.
