# Backend

The only runtime backend is backend/app, imported as app.* while commands run from backend/. There is no second root chemistry package.

## Commands

    python3.11 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    pytest -q
    uvicorn app.main:app --reload

Install requirements-optional.txt only when Claude, PubChem reference lookup, or RDKit conformer generation is required. Tests and curated analysis never require network or API keys.

## Layers

- app/chemistry: deterministic periodic table, valence, formal-charge, octet, resonance metadata, central-atom and VSEPR rules.
- app/data/curated_molecules.json: the single full golden-record source.
- app/services: resolver, Lewis validation, VSEPR, properties, 3D, explanation validation/fallback, and persistence.
- app/api/v1: mounted HTTP contract.

Every curated Lewis output is checked for electron conservation and formal-charge sum. Unknown composition does not trigger invented connectivity. External services provide identity/reference/coordinates only and never prove Lewis/VSEPR conclusions.

DATA_DIR contains feedback.jsonl and survey.jsonl. Writes use append mode, an exclusive lock, flush, and fsync. CSV export requires X-Teacher-Token matching TEACHER_EXPORT_TOKEN; an empty configured token disables export.
