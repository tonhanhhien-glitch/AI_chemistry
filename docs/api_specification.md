# API specification

Base path: `/api/v1`; OpenAPI UI: `/docs`. Domain failures use:

```json
{"detail":{"code":"UNSUPPORTED_MOLECULE","message":"..."}}
```

Ambiguity uses HTTP 409 and adds `detail.candidates`. FastAPI request-shape failures retain standard 422 responses. Formula/name inputs are capped at 80 characters.

## Endpoints

- `GET /health` — service status/version.
- `GET /formula?formula=SO4%5E2-` — strict syntax, inventory, and charge only.
- `GET /molecules/examples` and `GET /molecules/search?q=` — curated catalogue.
- `POST /analyze` — identity, Lewis, VSEPR, properties, 3D, optional explanation, and notices.
- `POST /explain` — explanation for a curated molecule ID.
- `GET /rules/vsepr`, `GET /rules/examples` — deterministic rule data.
- `POST /feedback`, `POST /survey`, `GET /teacher/export` — anonymous study workflow.

## Analyze request

```json
{
  "formula": "NF3",
  "include_explanation": false,
  "language": "en"
}
```

`molecule_id` selects a curated record. When a formula returns several valid PubChem identities, select the candidate without editing the original formula:

```json
{
  "formula": "NF3",
  "pubchem_cid": 24553,
  "include_explanation": false,
  "language": "en"
}
```

Resolution order is exact curated record, validated formula-aware PubChem identity, then conservative deterministic Lewis/VSEPR inference. Curated facts are never overwritten.

## Ambiguous response

```json
{
  "detail": {
    "code": "AMBIGUOUS_MOLECULE",
    "message": "The formula may represent several structures. Please pick a specific substance.",
    "candidates": [
      {
        "id": "pubchem:123",
        "cid": 123,
        "formula": "...",
        "charge": 0,
        "name_en": "...",
        "name_vi": "...",
        "canonical_smiles": "...",
        "source": "PubChem",
        "validation_status": "formula_charge_inventory_validated"
      }
    ]
  }
}
```

## Analysis response additions

The version remains `1.0` for compatibility. `molecule` includes canonical identity, CID, SMILES/InChI fields, validation status, cache timestamp, and typed connectivity. `vsepr.ideal_angle` remains temporarily; `vsepr.reference_angles` explicitly identifies teaching/reference values.

`structure3d.format` is `coordinates`, `molblock`, `sdf`, or `pdb`; `data` contains native model text where applicable. Source is one of `curated_coordinates`, `pubchem_3d`, `rdkit_etkdg`, or `idealized_vsepr`. Provenance includes `source_label`, `is_illustrative`, `is_computed`, `is_experimental`, `pubchem_cid`, and bilingual warnings.

`structure3d.angle_annotations` contains representative coordinate-derived angle classes and explicit atom triplets. Duplicate equivalent angles are omitted by default. `structure3d.electron_domains` contains bonding and illustrative lone-pair directions/positions; these do not alter molecular atom counts.

`notices.external_services_used` is `[]`, `["PubChem"]`, or `["PubChem", "RDKit"]` according to actual use. `external_service_statuses` exposes typed degradation/cache states without stack traces. `offline_capable` is true only when the same analysis can remain usable without its external identity source.

## Representative NF3 response (abridged only by unrelated property rows)

```json
{
  "schema_version": "1.0",
  "molecule": {
    "id": "pubchem:24553",
    "formula": "NF3",
    "charge": 0,
    "central_atom": "N",
    "source": "PubChem reference",
    "confidence": "medium",
    "pubchem_cid": 24553,
    "smiles": "N(F)(F)F",
    "canonical_identity": "GQPLMRYTRLFLPF-UHFFFAOYSA-N",
    "validation_status": "formula_charge_inventory_connectivity_lewis_vsepr_validated"
  },
  "lewis": {
    "total_valence_electrons": 26,
    "central_atom_id": "a0",
    "source": "validated_connectivity"
  },
  "vsepr": {
    "bonding_domains": 3,
    "lone_pair_domains": 1,
    "ax_en": "AX3E",
    "electron_geometry": "tetrahedral",
    "molecular_geometry": "trigonal pyramidal",
    "ideal_angle": "~107°"
  },
  "structure3d": {
    "format": "sdf",
    "source": "pubchem_3d",
    "source_label": "PubChem 3D conformer",
    "is_computed": true,
    "is_experimental": false,
    "pubchem_cid": 24553,
    "angle_annotations": [{"display_label": "109.5°", "category": "conformer"}],
    "electron_domains": [{"kind": "lone_pair", "is_illustrative": true}]
  },
  "notices": {
    "offline_capable": false,
    "external_services_used": ["PubChem"]
  }
}
```

The exact coordinate angle depends on the returned conformer; the backend calculates it from that conformer's coordinates and never copies `~107°` onto a mismatching arc.

## Formula grammar and stable errors

Flat canonical symbols with optional positive counts are supported. Charges are `+`, `-`, `^n+`, or `^n-`; repeated symbols accumulate. Parentheses, hydrates, isotopes, coefficients, and incorrect capitalization are rejected. Stable codes include `INVALID_FORMULA`, `UNSUPPORTED_FORMULA_SYNTAX`, `UNSUPPORTED_ELEMENT`, `UNSUPPORTED_MOLECULE`, `AMBIGUOUS_MOLECULE`, `EXTERNAL_RESOLUTION_FAILED`, and `CHEMISTRY_VALIDATION_ERROR`.
