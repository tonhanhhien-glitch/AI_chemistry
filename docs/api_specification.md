# API specification

Base path: /api/v1. OpenAPI: /docs. Chemistry errors use:

    { "detail": { "code": "UNSUPPORTED_MOLECULE", "message": "...", "candidates": [] } }

FastAPI request-shape errors retain its standard 422 response. Inputs are capped at 80 characters where applicable.

## Endpoints

- GET /health — service status/version.
- GET /formula?formula=SO4%5E2- — strict syntax, inventory, charge only.
- GET /molecules/examples — curated summaries.
- GET /molecules/search?q=nuoc — formula/name/alias search.
- POST /analyze — complete versioned pipeline.
- POST /explain — regenerate prose from an existing curated molecule ID.
- GET /rules/vsepr — all 13 supported rules.
- GET /rules/examples — curated rule examples.
- POST /feedback — anonymous rating/report.
- POST /survey — consented anonymous pre/post/Likert response.
- GET /teacher/export?kind=survey — CSV with X-Teacher-Token.

## Analyze

Request:

    {
      "formula": "H2O",
      "include_explanation": true,
      "explanation_level": "intermediate",
      "language": "vi"
    }

Use molecule_id instead of formula after candidate selection. The response schema_version is 1.0 and contains molecule, lewis, vsepr, properties, structure3d, explanation, and notices. Lewis atoms have stable IDs and 2D coordinates; 3D uses an atom/bond coordinate schema with source and is_illustrative.

Examples of controlled results: CO2 → AX2/linear/180°; H2O → AX2E2/bent/~104.5°; ClF3 → AX3E2/T-shaped; XeF4 → AX4E2/square planar.

## Formula grammar

Flat canonical symbols with optional positive counts. Supported charges: +, -, ^n+, ^n-. Repeated symbols accumulate. Parentheses, hydrates/dot notation, isotopes, coefficients, and incorrect capitalization are rejected rather than partially parsed.

Parsing does not infer identity: CH3COOH can parse while remaining unsupported by the curated analysis set. Stable codes include INVALID_FORMULA, UNSUPPORTED_FORMULA_SYNTAX, UNSUPPORTED_ELEMENT, UNSUPPORTED_MOLECULE, AMBIGUOUS_MOLECULE, and CHEMISTRY_VALIDATION_ERROR.

## Anonymous writes

Feedback requires rating 1–5 and a controlled category; comment max is 1000. Survey requires consent=true, phase pre/post/likert, and at most 30 answer keys. A missing or invalid session ID is replaced by a random UUID. Do not send names or student numbers.

Export returns UTF-8 CSV and prefixes spreadsheet-formula-like cells. If TEACHER_EXPORT_TOKEN is empty, export remains forbidden.

## Language and sources

Vietnamese is the default explanation language; English is optional. Property rows declare curated, computed, or PubChem reference provenance. Claude and idealized 3D outputs carry explicit disclaimers.
