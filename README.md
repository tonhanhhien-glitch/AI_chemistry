# VSEPR-AI

VSEPR-AI is being built as a chemistry teaching application. Rule-based
chemistry is the source of truth; AI will only be added later as an explanation
layer over verified results.

The current stabilization baseline intentionally implements one vertical slice:
a React form sends a formula to FastAPI, the strict parser validates atom counts
and charge, and the browser renders the result.

## Authoritative applications

`backend/app` is the only backend application. Run it from `backend/` with:

```bash
uvicorn app.main:app --reload
```

The frontend is the React + TypeScript + Vite application in `frontend/`.
Lewis structures, VSEPR inference, RDKit, PubChem, Claude, and 3D visualization
remain future work.

## Development

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload
```

In another terminal:

```bash
cd frontend
npm ci
cp .env.example .env
npm run lint
npm run build
npm run dev
```

The frontend is available at `http://localhost:5173`; its analysis page is
`/analysis`. API details and parser scope are documented in
[`docs/api_specification.md`](docs/api_specification.md).

## Docker

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker compose up --build
```
