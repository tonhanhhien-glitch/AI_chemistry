# Molecule Data Enrichment Guide

This guide covers only the **recommended source files to edit directly** when enriching molecule-specific information in the current codebase.

For normal molecule enrichment, use these four files:

```text
backend/app/data/curated_molecules.json
backend/app/data/chemical_identities.json
backend/app/data/experimental_geometries.json
backend/app/data/curated_properties.json
```

## Recommended order

1. `curated_molecules.json` — core Lewis/VSEPR and teaching data.
2. `experimental_geometries.json` — verified molecule-specific bond lengths, angles, and coordinates.
3. `chemical_identities.json` — CAS RN and searchable aliases.
4. `curated_properties.json` — reviewed physical/chemical properties and provenance.

---

## 1. `curated_molecules.json`

Path:

```text
backend/app/data/curated_molecules.json
```

Add or enrich records inside the top-level `molecules` array.

Use this file for:

- formula and charge
- English/Vietnamese names and aliases
- PubChem CID and SMILES
- atom inventory and atom order
- central atom
- total valence electrons
- Lewis bond orders
- lone pairs
- formal charges
- resonance
- octet exceptions
- VSEPR domains
- AXnEm
- electron geometry
- molecular geometry
- molecule-specific teaching/reference angle
- hybridization
- polarity and teaching notes

### Template

```json
{
  "review_status": "internal_golden_pending_expert_signoff",
  "pubchem_cid": null,
  "source": "curated",
  "confidence": "high",

  "hybridization_warning_vi": "Nhãn lai hoá là mô hình sư phạm gần đúng theo VSEPR, không phải mô tả liên kết hiện đại đầy đủ.",
  "hybridization_warning_en": "The hybridization label is an approximate VSEPR-style pedagogical model, not a full modern description of bonding.",

  "three_d_source": {
    "kind": "idealized_vsepr_template",
    "verified_reference": false
  },

  "id": "molecule-id",
  "name_vi": "Tên chất",
  "name_en": "English name",
  "aliases": ["common name"],

  "formula": "XY2",
  "charge": 0,

  "atom_inventory": {
    "X": 1,
    "Y": 2
  },

  "atom_symbols": ["X", "Y", "Y"],
  "central_atom": "X",

  "total_valence_electrons": 0,

  "bond_orders": [1, 1],
  "lone_pairs": [0, 0, 0],
  "formal_charges": [0, 0, 0],

  "resonance_forms": 1,
  "resonance_note_vi": null,

  "exception_flags": {
    "electron_deficient": false,
    "expanded_octet": false,
    "odd_electron": false
  },

  "bonding_domains": 2,
  "lone_pair_domains": 0,
  "steric_number": 2,

  "ax_en": "AX2",

  "electron_geometry": "linear",
  "molecular_geometry": "linear",
  "electron_geometry_vi": "thẳng",
  "molecular_geometry_vi": "thẳng",

  "ideal_angle": "180°",
  "distortion_note_vi": null,

  "hybridization": "sp",

  "polarity_note_vi": null,
  "polarity_note_en": null,

  "smiles": null,

  "teaching_note_vi": null,
  "teaching_note_en": null
}
```

### Important consistency rules

`atom_symbols[0]` must be the central atom.

For `N` atoms:

```text
len(atom_symbols)   = N
len(bond_orders)    = N - 1
len(lone_pairs)     = N
len(formal_charges) = N
```

Also:

```text
sum(formal_charges) = charge
```

and Lewis electron accounting should satisfy:

```text
2 × sum(bond_orders) + 2 × sum(lone_pairs)
= total_valence_electrons
```

VSEPR fields must agree:

```text
bonding_domains + lone_pair_domains = steric_number
```

A double or triple bond still counts as **one bonding domain**.

### Molecule-specific angle

`ideal_angle` can contain a concise molecule-specific teaching/reference value:

```json
"ideal_angle": "~107°"
```

or:

```json
"ideal_angle": "~102°"
```

Detailed measured geometry and provenance belong in `experimental_geometries.json`.

---

## 2. `experimental_geometries.json`

Path:

```text
backend/app/data/experimental_geometries.json
```

Add records inside the top-level `records` array.

Use this file for verified molecule-specific geometry:

- experimental bond lengths
- experimental bond angles
- multiple inequivalent angles
- dihedral angles
- Cartesian coordinates
- point group
- phase
- electronic state
- source/reference/URL

This is the recommended place for values such as the real `NH3`, `NF3`, or `ClF3` geometry.

### Template

```json
{
  "id": "source-molecule-reference",
  "evidence_type": "experimental",

  "identity": {
    "formula": "XY2",
    "charge": 0,

    "atom_inventory": {
      "X": 1,
      "Y": 2
    },

    "formula_identity_unambiguous": true,

    "cas_rn": null,
    "pubchem_cid": null,
    "inchi": null,
    "inchikey": null,

    "curated_molecule_id": "molecule-id"
  },

  "units": "angstrom",

  "phase": "gas",
  "electronic_state": null,
  "conformation": "equilibrium",
  "point_group": null,

  "atoms": [
    {"id": "a0", "element": "X", "role": "center"},
    {"id": "a1", "element": "Y", "role": "ligand"},
    {"id": "a2", "element": "Y", "role": "ligand"}
  ],

  "bonds": [
    {"atom1_id": "a0", "atom2_id": "a1", "order": 1},
    {"atom1_id": "a0", "atom2_id": "a2", "order": 1}
  ],

  "bond_lengths": [
    {
      "id": "mol-r1",
      "atom1_id": "a0",
      "atom2_id": "a1",
      "value_angstrom": 1.000,
      "equivalent_count": 2,
      "label": "X-Y"
    }
  ],

  "bond_angles": [
    {
      "id": "mol-a1",
      "atom1_id": "a1",
      "center_atom_id": "a0",
      "atom2_id": "a2",
      "value_deg": 100.00,
      "equivalent_count": 1,
      "label": "Y-X-Y"
    }
  ],

  "dihedrals": [],

  "coordinates": null,

  "source": {
    "name": "Source name",
    "reference": "Reference ID or publication",
    "url": "https://example.com/source",
    "comments": "Experimental gas-phase equilibrium geometry.",
    "retrieved_at": "2026-08-18T00:00:00Z"
  }
}
```

### Multiple inequivalent angles

Keep distinct angles as separate records. Do not average them.

Example for a T-shaped molecule:

```json
"bond_angles": [
  {
    "id": "mol-angle-1",
    "atom1_id": "a1",
    "center_atom_id": "a0",
    "atom2_id": "a2",
    "value_deg": 87.45,
    "equivalent_count": 2,
    "label": "axial-equatorial"
  },
  {
    "id": "mol-angle-2",
    "atom1_id": "a1",
    "center_atom_id": "a0",
    "atom2_id": "a3",
    "value_deg": 174.90,
    "equivalent_count": 1,
    "label": "axial-axial"
  }
]
```

### Coordinates

If verified Cartesian coordinates exist:

```json
"coordinates": [
  {"id": "a0", "element": "X", "x": 0.0, "y": 0.0, "z": 0.0},
  {"id": "a1", "element": "Y", "x": 1.0, "y": 0.0, "z": 0.0},
  {"id": "a2", "element": "Y", "x": -0.2, "y": 0.98, "z": 0.0}
]
```

Otherwise:

```json
"coordinates": null
```

Every coordinate ID must match an atom in `atoms`.

Only use:

```json
"evidence_type": "experimental"
```

for genuinely experimental geometry.

---

## 3. `chemical_identities.json`

Path:

```text
backend/app/data/chemical_identities.json
```

Add entries inside the top-level `identities` array.

Use this file for:

- formula
- charge
- curated molecule ID
- CAS Registry Number
- English/Vietnamese names
- common and alternative search names

### Template

```json
{
  "formula": "XY2",
  "charge": 0,

  "curated_molecule_id": "molecule-id",

  "cas_rn": "1234-56-7",

  "names": [
    "English name",
    "Tên tiếng Việt",
    "common name",
    "alternative name"
  ]
}
```

If CAS RN is not verified:

```json
"cas_rn": null
```

Keep these synchronized with `curated_molecules.json`:

```text
formula
charge
curated_molecule_id
```

Example:

```json
{
  "formula": "NH3",
  "charge": 0,
  "curated_molecule_id": "nh3",
  "cas_rn": "7664-41-7",
  "names": [
    "ammonia",
    "amoniac"
  ]
}
```

---

## 4. `curated_properties.json`

Path:

```text
backend/app/data/curated_properties.json
```

Add properties inside the top-level `properties` object.

The species key format is:

```text
<formula>|<charge>
```

Examples:

```text
H2O|0
NH3|0
NH4+|1
NO3-|-1
CO3^2-|-2
```

Use this file for reviewed molecule-specific properties such as:

- physical state
- appearance
- odor
- melting point
- boiling point
- density
- vapor pressure
- dipole moment
- solubility
- other physical/chemical properties

### Template

```json
"XY2|0": [
  {
    "key": "physical_state",
    "category": "physical",

    "label_vi": "Trạng thái vật lý",
    "label_en": "Physical state",

    "value": "Gas",
    "value_vi": "Khí",
    "value_en": "Gas",

    "evidence_type": "experimental",

    "source_name": "Source name",
    "source_reference": "Reference",
    "source_url": "https://example.com/source",

    "retrieved_at": "2026-08-18T00:00:00Z"
  },

  {
    "key": "boiling_point",
    "category": "physical",

    "label_vi": "Nhiệt độ sôi",
    "label_en": "Boiling point",

    "value": -10.0,
    "unit": "°C",

    "conditions": {
      "pressure": "760 mmHg"
    },

    "evidence_type": "experimental",

    "source_name": "Source name",
    "source_reference": "Reference",
    "source_url": "https://example.com/source",

    "retrieved_at": "2026-08-18T00:00:00Z"
  },

  {
    "key": "dipole_moment",
    "category": "chemical",

    "label_vi": "Moment lưỡng cực",
    "label_en": "Dipole moment",

    "value": 1.00,
    "unit": "D",

    "evidence_type": "experimental",

    "source_name": "Source name",
    "source_reference": "Reference",
    "source_url": "https://example.com/source",

    "retrieved_at": "2026-08-18T00:00:00Z"
  }
]
```

### Categories

Use one of the normalized categories used by the current property model:

```text
identity
structural
physical
chemical
```

### Evidence

Use appropriate provenance, for example:

```text
experimental
source_annotation
computed
curated
deterministic
```

Do not mark a calculated or descriptive value as experimental.

### Conditions

Preserve relevant conditions:

```json
"conditions": {
  "temperature": "25 °C",
  "pressure": "760 mmHg"
}
```

Keep source name, reference, URL, unit, and retrieval date whenever available.

### Ions

Be careful with bulk physical properties for isolated molecular ions.

Do not copy melting point, boiling point, density, or similar values from a salt/solution and present them as properties of the isolated ion.

---

## 5. Keep the files synchronized

For the same molecule, identity must remain consistent.

Example for `NF3`:

### `curated_molecules.json`

```json
{
  "id": "nf3",
  "formula": "NF3",
  "charge": 0
}
```

### `chemical_identities.json`

```json
{
  "formula": "NF3",
  "charge": 0,
  "curated_molecule_id": "nf3"
}
```

### `experimental_geometries.json`

```json
"identity": {
  "formula": "NF3",
  "charge": 0,
  "curated_molecule_id": "nf3"
}
```

### `curated_properties.json`

```json
"NF3|0": [
  ...
]
```

The most important shared fields are:

```text
formula
charge
curated molecule ID
atom inventory
CAS RN
PubChem CID
```

---

## 6. Minimum recommended enrichment

For a new molecule, first complete `curated_molecules.json` with:

```text
formula and charge
names
atom inventory
central atom
Lewis structure
formal charges
resonance
AXnEm
electron geometry
molecular geometry
molecule-specific teaching angle
polarity
teaching notes
```

Then add:

```text
experimental_geometries.json
```

when reliable bond lengths/angles are available.

Add:

```text
chemical_identities.json
```

for CAS RN and searchable aliases.

Add:

```text
curated_properties.json
```

when reliable property values and sources are available.

---

## 7. Validate after editing

From the backend directory:

```bash
cd backend
pytest -q tests/test_catalog_integrity.py
```

Also recommended:

```bash
pytest -q tests/test_golden_pipeline.py
pytest -q tests/test_reference_bond_angle.py
pytest -q tests/test_geometry_evidence.py
pytest -q tests/test_properties.py
```

For a complete validation:

```bash
pytest -q
```

---

## 8. Final checklist

Before committing a molecule:

- [ ] Formula and charge are correct.
- [ ] Molecule ID is unique.
- [ ] Atom inventory matches the formula.
- [ ] Central atom is first in `atom_symbols`.
- [ ] Lewis bond orders are correct.
- [ ] Lone-pair counts are correct.
- [ ] Formal charges are correct and sum to total charge.
- [ ] Total valence-electron count is correct.
- [ ] Resonance information is correct.
- [ ] VSEPR domain counts are correct.
- [ ] AXnEm is correct.
- [ ] Electron geometry is correct.
- [ ] Molecular geometry is correct.
- [ ] Molecule-specific angle is correct.
- [ ] Experimental angles/lengths include provenance.
- [ ] Multiple inequivalent angles remain separate.
- [ ] CAS RN and external identifiers are verified.
- [ ] Property values preserve units and conditions.
- [ ] Property values include a source.
- [ ] Identity is consistent across all enriched files.
- [ ] `pytest -q tests/test_catalog_integrity.py` passes.
- [ ] Full backend tests pass before merging.

---

## Recommended files summary

For normal manual molecule enrichment, focus only on:

```text
backend/app/data/curated_molecules.json
backend/app/data/experimental_geometries.json
backend/app/data/chemical_identities.json
backend/app/data/curated_properties.json
```

Together they provide:

```text
Core Lewis/VSEPR data
+ experimental geometry
+ searchable identity
+ curated physical/chemical properties
```
