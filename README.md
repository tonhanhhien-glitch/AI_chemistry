# VSEPRLab

VSEPRLab is a Vietnamese-first Lewis/VSEPR learning application for second-year chemistry students. The deterministic chemistry engine under backend/app is the source of truth; Claude can explain verified facts but cannot decide structures, charges, AXnEm classifications, geometries, or angles.

## What works

- Strict flat-formula and ion parser with stable Vietnamese errors.
- 16 curated records covering the required formula families and all 13 supported AXnEm cases.
- End-to-end POST /api/v1/analyze: identity → Lewis → VSEPR → properties → illustrative 3D → optional explanation.
- Offline operation for every curated example; PubChem, RDKit, and Claude are feature-flagged and fail closed.
- Vietnamese React UI with Lewis SVG, 3Dmol.js controls/fallback, examples, rules, feedback, consented survey, and teacher CSV export.
- Locked append-only JSONL study persistence with anonymous UUID sessions and CSV formula-injection protection.
- Backend and frontend tests plus GitHub Actions CI.

Golden records are marked internal_golden_pending_expert_signoff. They are reviewable and tested, but are not represented as externally expert-approved. No PubChem CID is shown without source verification.

## Local development

Backend (Python 3.11+):

    cd backend
    python3.11 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    pytest -q
    uvicorn app.main:app --reload

Frontend (Node 20 LTS):

    cd frontend
    npm ci
    npm test
    npm run lint
    npm run build
    npm run dev

Open http://localhost:5173; OpenAPI is at http://localhost:8000/docs. Optional external packages are in backend/requirements-optional.txt.

## Docker Compose

    cp .env.example .env
    docker compose up --build

Open http://localhost:8080. Replace TEACHER_EXPORT_TOKEN first. Study data is in the study-data volume; Compose defaults do not call external APIs.

## Environment

- CORS_ORIGINS: comma-separated browser origins.
- DATA_DIR: writable JSONL study directory.
- TEACHER_EXPORT_TOKEN: protects CSV export; empty disables export.
- ANTHROPIC_API_KEY and ENABLE_CLAUDE: optional explanation integration.
- ENABLE_PUBCHEM / ENABLE_RDKIT: optional reference/coordinate adapters.
- VITE_API_BASE_URL: API URL baked into the frontend build.

Never commit .env, runtime JSONL, or real survey exports.

## Scope and limitations

Curated formulas: CO2, BF3, SO2, H2O, NH3, CH4, NH4+, PCl5, SF4, ClF3, XeF2, SF6, BrF5, XeF4, NO3-, and CO3^2-. Formula syntax is flat. Parentheses, hydrates, isotopes, coefficients, transition-metal complexes, clusters, organometallics, and arbitrary connectivity inference are unsupported.

Idealized 3D fallbacks illustrate VSEPR geometry; they are not optimized quantum structures. sp3d/sp3d2 labels are pedagogical VSEPR-era approximations. LLM text is explanatory.

See docs/chemistry_scope.md, docs/system_architecture.md, docs/api_specification.md, docs/validation_protocol.md, docs/teacher_guide.md, and docs/student_guide.md.
