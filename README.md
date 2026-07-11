# VSEPR-AI

A web app that teaches Lewis structures and VSEPR molecular geometry, using
chemistry rules as the source of truth and AI (Claude) only as an
explanation layer on top of verified results.

## Stack

- **Backend**: FastAPI + RDKit + PubChemPy + Anthropic Claude API (`backend/`)
- **Frontend**: React + TypeScript + Vite + 3Dmol.js (`frontend/`)

## Project layout

```
backend/    FastAPI service: chemistry rule engine, PubChem/RDKit integration, Claude explanations, REST API
frontend/   React app: formula input, Lewis/VSEPR viewers, 3D molecule viewer, explanation panel
docs/       Architecture, API spec, chemistry scope, and evaluation documentation
deployment/ Nginx config and hosting-provider deployment files
```

See `docs/system_architecture.md` for the full design and `docs/api_specification.md`
for the REST API contract. Implementation checklists live in the project plan.

## Getting started

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in ANTHROPIC_API_KEY
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env   # set VITE_API_BASE_URL
npm run dev
```

### Docker

```bash
docker compose up --build
```
