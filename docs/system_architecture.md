# System architecture

    React/Vite UI
        | versioned JSON /api/v1
    FastAPI routes
        |
    analysis service
        + strict parser -> central element registry
        + curated resolver -> curated_molecules.json
        + Lewis validator -> valence/formal-charge/octet rules
        + VSEPR engine -> complete AXnEm table
        + property service -> provenance-tagged facts
        + 3D service -> ideal VSEPR coordinates
        + explanation -> deterministic fallback or Claude

The dependency direction is deliberate: AI consumes an immutable fact bundle after chemistry analysis and cannot feed conclusions back. Claude output is checked for formula, AXnEm, geometry, and angle contradictions, retried once, then replaced with a deterministic template on failure.

Curated resolution happens first. PubChem is only a reference/candidate source with timeout and corruption-tolerant cache. RDKit accepts validated SMILES only. Neither proves a teaching conclusion. Application import makes no external calls.

The frontend uses backend-aligned types. 3Dmol.js consumes atom coordinates and provides rotate/zoom, style, label, reset, fullscreen, touch, and WebGL fallback behavior.

Feedback/survey data is separate from caches. The MVP uses a writable directory, locked append-only JSONL, and token-protected sanitized CSV. A future migration can replay rows into SQLite and later PostgreSQL using session UUID and timestamp as stable keys; no migration framework is needed now.
