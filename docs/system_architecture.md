# System architecture

```text
React/Vite UI
    | versioned JSON /api/v1
FastAPI routes (backend/app only)
    |
analysis service
    + strict formula/charge parser
    + curated resolver (authoritative teaching facts)
    + formula-aware PubChem resolver and typed status/cache
    + conservative deterministic connectivity/Lewis/VSEPR engine
    + 3D resolver: PubChem SDF -> RDKit ETKDGv3 -> VSEPR template
    + property service with per-item provenance
    + explanation layer over immutable facts
```

## Trust boundary

Curated records win and PubChem never silently overwrites their Lewis or VSEPR conclusions. Uncurated PubChem candidates must match normalized atom inventory and total charge, must describe one covalent unit when that metadata is present, and must pass the supported-chemistry validator. Several valid candidates produce a structured 409; none is selected by result order. The deterministic fallback may run after PubChem is disabled or returns no matching candidate, but only when the formula itself has a unique supported atom inventory. The engine is limited to unique, closed-shell, single-center main-group star connectivity with terminal H/halogen single bonds and steric number at most six. Failure is explicit rather than fabricated.

The LLM is downstream-only. It receives immutable deterministic facts, its prose is checked for contradictions, and a deterministic explanation replaces unavailable or contradictory output.

## External services and cache

PubChem uses PUG REST `fastformula` for identity and a CID-specific 3D SDF request with `record_type=3d`. Requests have a timeout, process-level rate limiting, and bounded retry only for 429/503/5xx or transport failures; 400/404 are permanent. Identity and CID/record-type structures use corruption-tolerant atomic JSON caches under `CACHE_DIR`, expiring after `PUBCHEM_CACHE_TTL_SECONDS`. Typed states distinguish disabled, cache hit, not found, ambiguous, timeout, rate limited, temporary failure, invalid response, formula mismatch, and unavailable conformers.

RDKit is optional and receives only validated SMILES. It adds explicit hydrogen atoms, embeds with ETKDGv3 and a fixed seed, then optimizes with MMFF or UFF. Output is a computed MolBlock, never experimental data.

## 3D and educational overlays

`Structure3D` carries format/data, parsed atoms and bonds, source enum, source label, computed/illustrative/experimental flags, CID, central atom, coordinate-derived representative angle classes, and electron-domain annotations. SDF, MolBlock, PDB, and local coordinate responses are loaded using their real 3Dmol formats.

Angle arcs are built from the same atom coordinates used for rendering. Teaching/reference VSEPR angles remain separate. Lone-pair lobes use deterministic VSEPR orientation and are independent translucent shapes; they never enter the molecule atom count or SDF/MolBlock.

## Offline behavior

Curated records remain usable with PubChem and RDKit disabled and fall back to VSEPR coordinates. `notices.offline_capable` is true for these analyses. An uncurated identity first obtained from PubChem reports false even if its returned structure falls back to VSEPR. `external_services_used` lists only services that materially supplied identity or coordinates.
