# Backend

`app` is the only authoritative FastAPI application. The production analyzer is curated-first, then validates formula-aware PubChem candidates, then applies a deliberately conservative deterministic Lewis/VSEPR engine. 3D priority is the reviewed local experimental snapshot, PubChem 3D SDF, RDKit ETKDGv3 MolBlock, then an idealized VSEPR coordinate template. Automated tests never make live network calls.

## Run and test

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload
```

Install `requirements-optional.txt` and set `ENABLE_RDKIT=true` for RDKit conformers. For Docker, also set the build-time `INSTALL_RDKIT=true` so the optional wheel is installed. Set `ENABLE_PUBCHEM=true` for uncurated identity and PubChem 3D lookup; PubChem requires outbound HTTPS but no key. `PUBCHEM_TIMEOUT_SECONDS`, `PUBCHEM_CACHE_TTL_SECONDS`, `PUBCHEM_MAX_REQUESTS_PER_SECOND`, `PUBCHEM_MAX_CANDIDATES`, and `PUBCHEM_RETRY_COUNT` control safe network behavior. With both flags false, curated molecules remain functional; verified NH3 and formula-matched NF3 use local NIST coordinates, and other molecules use idealized coordinates. Cache files under `CACHE_DIR` are keyed by formula identity or CID/record type and expire by TTL.

Schema 1.1 returns bond_angles with preferred, experimental, coordinate_derived, and vsepr_prediction groups. A rendered-coordinate angle is computed from the actual returned coordinates. Experimental NIST values, curated molecule references, computed conformers, general VSEPR predictions, and idealized-coordinate angles are kept separate; PubChem and RDKit are never experimental. Lone-pair 3D domains are illustrative annotations, not atoms or quantum density.

# Backend Task Checklist

## Setup

- [x] Create `backend/` folder.
- [x] Initialize Python environment.
- [x] Install FastAPI.
- [x] Install Uvicorn.
- [x] Install Pydantic.
- [x] Install RDKit.
- [x] Install PubChemPy.
- [x] Call OpenRouter over httpx (no extra SDK).
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
- [x] Search molecule using formula-aware PubChem PUG REST second.
- [x] Use RDKit for 3D conformer fallback when validated SMILES is available.
- [x] Use VSEPR template fallback if PubChem/RDKit 3D fails.
- [x] Cache PubChem results.
- [x] Return molecule identity, formula, SMILES, CID, validation, and properties.
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

- [x] Generate 3D structure using RDKit when validated SMILES is available.
- [x] Retrieve and cache PubChem 3D SDF when available.
- [x] Use VSEPR geometry template if automatic 3D generation fails.
- [x] Return native MolBlock/SDF plus coordinate-compatible data.
- [x] Return atom coordinates.
- [x] Return bond data.
- [x] Return rendering metadata for 3Dmol.js.
- [x] Add warning for illustrative 3D models.
- [x] Cache PubChem identity and CID/record-type structures.
- [x] Write tests for 3D generation.

## AI Explanation Service (`app/services/ai_explanation_service.py`, `app/prompts/`)

- [x] Create prompt templates.
- [x] Add explanation levels: Basic, Intermediate, Advanced.
- [x] Send only verified backend facts to the OpenRouter API.
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
- [x] Test PubChem behavior with network-free mocks.
- [x] Test RDKit priority and fallback with network-free mocks.
- [x] Test Lewis output.
- [x] Test VSEPR output.
- [ ] Test AI prompt.
- [x] Test API response schema.
- [x] Test full pipeline.
- [x] Build golden molecule test set.
- [ ] Ask chemistry expert to validate golden set.
