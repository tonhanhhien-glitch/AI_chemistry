# API specification

Base path: `/api/v1`; OpenAPI UI: `/docs`. Domain failures use:

```json
{"detail":{"code":"UNSUPPORTED_MOLECULE","message":"..."}}
```

Ambiguity uses HTTP 409 and adds `detail.candidates`. FastAPI request-shape failures retain standard 422 responses. Formula/name inputs are capped at 80 characters.

## Endpoints

- `GET /health` — service status/version plus `integrations.pubchem_enabled` and `integrations.rdkit_enabled`.
- `GET /formula?formula=SO4%5E2-` — strict syntax, inventory, and charge only.
- `GET /molecules/examples` and `GET /molecules/search?q=` — curated catalogue.
- `POST /analyze` — identity, Lewis, VSEPR, properties, 3D, optional explanation, and notices.
- `POST /explain` and `POST /chat` — grounded follow-ups using `molecule_id` or `formula`, with optional `pubchem_cid`.
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

The analysis schema version is `1.1`. `molecule` includes canonical identity, CID, SMILES/InChI fields, validation status, cache timestamp, and typed connectivity. `vsepr.ideal_angle` remains temporarily; `vsepr.reference_angles` explicitly identifies teaching/reference values.

`structure3d.format` is `coordinates`, `molblock`, `sdf`, or `pdb`; `data` contains native model text where applicable. Source is one of `curated_coordinates`, `pubchem_3d`, `rdkit_etkdg`, or `idealized_vsepr`. Provenance includes `source_label`, `is_illustrative`, `is_computed`, `is_experimental`, `pubchem_cid`, and bilingual warnings.

`bond_angles` is the schema 1.1 evidence contract: preferred follows experimental → curated reference → PubChem/RDKit conformer → general VSEPR; experimental, coordinate_derived, and vsepr_prediction preserve parallel evidence. `structure3d.reference_bond_angle` is the normalized molecule-specific angle behind that preference order — experimental measurement, curated molecule-specific reference, or `ideal_vsepr` when only the generic AXnEm value exists — and is what the idealized fallback model is shaped to, so the header and the 3D overlay never disagree (H2O bends to 104.5°, not the 109.5° electron-domain ideal). It is absent for geometries with several inequivalent angles. `structure3d.angle_annotations` contains coordinate-derived classes and explicit atom triplets; symmetry-equivalent values carry equivalent_count, while genuinely distinct values remain separate. `structure3d.electron_domains` contains bonding and illustrative lone-pair directions/positions; these do not alter molecular atom counts.

`notices.external_services_used` is `[]`, `["PubChem"]`, or `["PubChem", "RDKit"]` according to actual use. `external_service_statuses` exposes typed degradation/cache states without stack traces. `offline_capable` is true only when the same analysis can remain usable without its external identity source.

## Representative NF3 response (abridged only by unrelated property rows)

```json
{
  "schema_version": "1.1",
  "molecule": {
    "id": "deterministic:nf3",
    "formula": "NF3",
    "charge": 0,
    "central_atom": "N",
    "source": "deterministic",
    "confidence": "medium",
    "pubchem_cid": null,
    "smiles": null,
    "canonical_identity": null,
    "validation_status": "formula_unique_scope_lewis_vsepr_validated"
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
    "ideal_angle": "<109.5°"
  },
  "structure3d": {
    "format": "coordinates",
    "source": "curated_coordinates",
    "source_label": "NIST CCCBDB experimental gas-phase geometry",
    "is_computed": false,
    "is_experimental": true,
    "pubchem_cid": 24553,
    "reference_bond_angle": {"value_deg": 102.37, "display_label": "102.37°", "category": "measured"},
    "angle_annotations": [{"display_label": "102.4°", "category": "measured", "equivalent_count": 3}],
    "electron_domains": [{"kind": "lone_pair", "is_illustrative": true}]
  },
  "bond_angles": {
    "preferred": [{
      "atom1_element": "F", "center_element": "N", "atom2_element": "F",
      "value_deg": 102.37, "display_label": "102.37°",
      "evidence_type": "experimental", "source_name": "NIST CCCBDB",
      "source_url": "https://cccbdb.nist.gov/exp2x.asp?casno=7783542",
      "reference": "1998Kuc", "phase": "gas",
      "is_experimental": true, "is_computed": false, "equivalent_count": 3
    }],
    "experimental": [{"display_label": "102.37°", "evidence_type": "experimental"}],
    "coordinate_derived": [{"display_label": "102.4°", "atom1_id": "a2", "center_atom_id": "a0", "atom2_id": "a3"}],
    "vsepr_prediction": [{"display_label": "<109.5°", "evidence_type": "ideal_vsepr"}],
    "selection_reason": "Local experimental geometry is the highest-priority molecule-specific evidence."
  },
  "notices": {
    "offline_capable": true,
    "external_services_used": []
  }
}
```

The preferred 102.37° value is the sourced NIST record. The rendered 102.4° annotation is independently recalculated from the stored coordinates; the general <109.5° AX3E prediction is not painted onto that arc.

## Formula grammar and stable errors

Flat canonical symbols with optional positive counts are supported. Charges are `+`, `-`, `^n+`, or `^n-`; repeated symbols accumulate. Parentheses, hydrates, isotopes, coefficients, and incorrect capitalization are rejected. Stable codes include `INVALID_FORMULA`, `UNSUPPORTED_FORMULA_SYNTAX`, `UNSUPPORTED_ELEMENT`, `UNSUPPORTED_MOLECULE`, `AMBIGUOUS_MOLECULE`, `EXTERNAL_RESOLUTION_FAILED`, and `CHEMISTRY_VALIDATION_ERROR`.
