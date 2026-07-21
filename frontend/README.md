# Frontend

React 18 + TypeScript + Vite, with Vietnamese as the default visible language and 3dmol as the interactive viewer.

    npm ci
    cp .env.example .env
    npm test
    npm run lint
    npm run build
    npm run dev

VITE_API_BASE_URL is read at build time. The production Docker image defaults to /api/v1 and serves the SPA through nginx.

Implemented pages: Home, full Analysis workflow, geometry-grouped Examples, complete VSEPR Rules, consented anonymous Survey, and accessible 404. Analysis includes loading/retry/candidate states, Lewis SVG, AXnEm cards, 3D controls/fallback, provenance-separated properties, explanation levels/regeneration/copy, and feedback.

Tests cover input validation, full analysis rendering, 3D fallback, deterministic explanation notice, structured ambiguity mapping, feedback, and consented survey submission. Teacher export is backend-only so the browser never stores the export token.
