# VSEPR-AI

VSEPR-AI is a bilingual chemistry teaching application that connects formula parsing, validated molecular identity, Lewis electron accounting, VSEPR classification, and educational 3D visualization. Deterministic rules and reviewed records are authoritative; an LLM may explain the finished fact bundle but cannot decide identity, bonds, formal charge, Lewis structure, AXnEm, geometry, or angles.

## Authoritative applications

`backend/app` is the only FastAPI application. `frontend/` is the React + TypeScript + Vite application. No parallel API or replacement backend is used.

## Resolution and 3D priority

Analysis resolves a molecule in this order:

1. An exact verified record in `backend/app/data/curated_molecules.json`. Curated Lewis/VSEPR facts and review status are preserved.
2. When `ENABLE_PUBCHEM=true`, formula-aware PubChem candidates are checked against formula, charge, atom inventory, one-covalent-unit metadata, and project scope. One valid candidate continues; multiple valid candidates produce HTTP 409 and a CID selection panel.
3. A conservative deterministic engine handles only unique, closed-shell, single-center main-group star connectivity within AXnEm and steric number 2–6. It refuses unsupported or non-unique chemistry.

Coordinates use a reviewed local experimental geometry first, then validated PubChem 3D SDF, an optional deterministic-seed RDKit ETKDGv3 conformer (MMFF, otherwise UFF), and finally an idealized VSEPR template. Every response states its source and whether it is computed, illustrative, or experimental. PubChem computed conformers are not described as experimental.

## Scientific display model

The angle arc is calculated only from the coordinates currently rendered. The top-level schema 1.1 bond_angles bundle separately ranks experimental, curated molecule-specific, computed-conformer, and idealized evidence while retaining the general VSEPR prediction. NF3 therefore prefers experimental F–N–F = 102.37° and NH3 prefers experimental H–N–H = 106.67°; both still show the general AX3E prediction <109.5°. Lewis dots represent valence electrons in a 2D bookkeeping model. VSEPR lone-pair lobes represent illustrative electron domains and are not atoms, electron trajectories, or calculated quantum electron-density surfaces.

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
npm test
npm run lint
npm run build
npm run dev
```

For optional RDKit support, install `backend/requirements-optional.txt` (or a compatible RDKit build for the deployment platform) and set `ENABLE_RDKIT=true`. PubChem needs outbound HTTPS but no API key. With both integrations disabled, curated records remain usable; NH3 and deterministic NF3 use the reviewed local NIST snapshots, while records without local coordinates use idealized VSEPR coordinates. Live deployment examples enable PubChem, but CI keeps PubChem and RDKit disabled. GET /api/v1/health reports both integration flags.

See [API specification](docs/api_specification.md), [system architecture](docs/system_architecture.md), and [chemistry scope](docs/chemistry_scope.md).
