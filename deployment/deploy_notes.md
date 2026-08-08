# Deployment notes

## Release gate

Run backend pytest, frontend npm test/lint/build, docker compose config, and image builds. Confirm external flags are false for the offline smoke test, teacher export is forbidden without a token, and runtime data is not in Git.

## Configuration

Set CORS_ORIGINS to the exact frontend origin, DATA_DIR to persistent writable storage, and TEACHER_EXPORT_TOKEN to a long random secret. Set VITE_API_BASE_URL before the frontend build; Vite variables cannot be changed at container runtime without rebuilding.

The AI explanation and chat layer calls OpenRouter first and OpenAI as the fallback. OpenRouter requires OPENROUTER_API_KEY plus ENABLE_OPENROUTER=true; OpenAI requires OPENAI_API_KEY plus ENABLE_OPENAI=true. Both remain disabled in checked-in deployment examples. OpenAI is only contacted when the OpenRouter call fails (timeout, rate limit, exhausted credit, provider error) or when ENABLE_OPENROUTER=false, so the paid key stays idle while the free tier works; enabling either alone is valid, and with both disabled every answer comes from the deterministic template. OPENROUTER_MODEL (default google/gemma-4-31b-it:free) and OPENAI_MODEL (default gpt-4o-mini) select the models and can be changed without touching Python source. Live lookup configurations set ENABLE_PUBCHEM=true; CI explicitly sets ENABLE_PUBCHEM=false and ENABLE_RDKIT=false. PubChem/RDKit are optional and must never be required for curated analysis. Install optional backend dependencies when enabling them.

## Smoke test

Check health and confirm its PubChem/RDKit enabled flags match the intended environment; analyze NF3 and verify experimental 102.37° plus general <109.5°; analyze CO2 and XeF4, submit disposable feedback/survey rows, export both CSV kinds with the teacher token, test a 403 without it, and inspect the 3D warning. Verify mobile navigation and WebGL fallback.

## Recovery and migration

Back up the DATA_DIR volume. JSONL is append-only; recover by restoring files. For a future database migration, import each valid JSON object into SQLite/PostgreSQL using session_id and submitted_at, retain the raw backup, compare row counts, then switch writers only after validation.
