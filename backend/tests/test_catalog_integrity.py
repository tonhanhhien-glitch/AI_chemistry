"""Catalog-wide invariants for the curated molecule, geometry and property data.

These tests treat ``curated_molecules.json``, ``experimental_geometries.json`` and
``curated_properties.json`` as a dataset that must stay internally consistent as the
catalog grows -- not just "does today's data happen to work", but "can a bad edit to
any one field ever slip past the test suite". Chemistry correctness (electron
counting, formal charges, AXnEm classification) is re-derived independently from the
deterministic engine rather than merely echoed back from the record under test.
"""

from __future__ import annotations

import pytest

from app.chemistry.formal_charge import validate_formal_charge_sum
from app.chemistry.valence_rules import total_valence_electrons
from app.chemistry.vsepr_rules import get_vsepr_rule
from app.geometry.fitter import fit_cartesian_coordinates
from app.geometry.providers.nist_cccbdb import snapshot_records
from app.properties.providers.curated import _catalog as curated_property_catalog
from app.schemas.geometry_evidence_schema import MolecularGeometryEvidence
from app.services.formula_parser import parse_formula
from app.services.molecule_resolver import curated_records

RECORDS = list(curated_records())
RECORD_IDS = [record["id"] for record in RECORDS]


@pytest.mark.parametrize("record", RECORDS, ids=RECORD_IDS)
def test_formula_parses_and_matches_declared_charge(record: dict) -> None:
    parsed = parse_formula(record["formula"])
    assert parsed.charge == record["charge"]
    assert parsed.atoms == record["atom_inventory"]


@pytest.mark.parametrize("record", RECORDS, ids=RECORD_IDS)
def test_atom_inventory_matches_atom_symbols(record: dict) -> None:
    counts: dict[str, int] = {}
    for symbol in record["atom_symbols"]:
        counts[symbol] = counts.get(symbol, 0) + 1
    assert counts == record["atom_inventory"]
    assert record["atom_symbols"][0] == record["central_atom"]


@pytest.mark.parametrize("record", RECORDS, ids=RECORD_IDS)
def test_bond_lone_pair_and_formal_charge_arrays_align_with_atoms(record: dict) -> None:
    n_atoms = len(record["atom_symbols"])
    assert len(record["bond_orders"]) == n_atoms - 1
    assert len(record["lone_pairs"]) == n_atoms
    assert len(record["formal_charges"]) == n_atoms


@pytest.mark.parametrize("record", RECORDS, ids=RECORD_IDS)
def test_formal_charges_sum_to_the_declared_charge(record: dict) -> None:
    validate_formal_charge_sum(record["formal_charges"], record["charge"])


@pytest.mark.parametrize("record", RECORDS, ids=RECORD_IDS)
def test_total_valence_electrons_matches_independent_computation(record: dict) -> None:
    expected = total_valence_electrons(record["atom_inventory"], record["charge"])
    assert record["total_valence_electrons"] == expected
    # The Lewis structure itself must also account for exactly that many electrons:
    # each bond order contributes 2 electrons per order, each lone pair contributes 2.
    represented = 2 * sum(record["bond_orders"]) + 2 * sum(record["lone_pairs"])
    assert represented == expected


@pytest.mark.parametrize("record", RECORDS, ids=RECORD_IDS)
def test_domain_counts_agree_with_steric_number_and_axnem(record: dict) -> None:
    assert record["bonding_domains"] + record["lone_pair_domains"] == record["steric_number"]
    rule = get_vsepr_rule(record["bonding_domains"], record["lone_pair_domains"])
    assert record["ax_en"] == rule.ax_en
    assert record["electron_geometry"] == rule.electron_geometry
    assert record["electron_geometry_vi"] == rule.electron_geometry_vi
    assert record["molecular_geometry"] == rule.molecular_geometry
    assert record["molecular_geometry_vi"] == rule.molecular_geometry_vi
    # bonding_domains must equal the number of ligand atoms actually drawn.
    assert record["bonding_domains"] == len(record["atom_symbols"]) - 1


@pytest.mark.parametrize("record", RECORDS, ids=RECORD_IDS)
def test_exception_flags_are_chemically_consistent(record: dict) -> None:
    """Cross-check each flag against the electron count actually drawn on the central atom.

    "Expanded octet" is about electrons around the central atom exceeding eight -- not
    directly about the domain count, since a double/triple bond is one VSEPR domain but
    contributes more than two electrons to that count.
    """

    flags = record["exception_flags"]
    central_electron_count = 2 * record["lone_pairs"][0] + 2 * sum(record["bond_orders"])
    if flags["expanded_octet"]:
        assert central_electron_count > 8, f"{record['id']}: expanded_octet flagged but only {central_electron_count} electrons drawn"
    elif not flags["electron_deficient"]:
        assert central_electron_count <= 8, (
            f"{record['id']}: {central_electron_count} electrons on the central atom but neither "
            "expanded_octet nor electron_deficient is flagged"
        )
    if flags["electron_deficient"]:
        assert central_electron_count < 8, f"{record['id']}: electron_deficient flagged but {central_electron_count} electrons drawn"
    assert isinstance(flags["odd_electron"], bool)
    if flags["odd_electron"]:
        assert record["total_valence_electrons"] % 2 == 1


@pytest.mark.parametrize("record", RECORDS, ids=RECORD_IDS)
def test_resonance_metadata_is_internally_consistent(record: dict) -> None:
    forms = record.get("resonance_forms", 1)
    assert forms >= 1
    note_vi, note_en = record.get("resonance_note_vi"), record.get("resonance_note_en")
    if forms > 1:
        assert note_vi and note_en, f"{record['id']}: {forms} resonance forms but no bilingual note"
    else:
        assert note_vi is None and note_en is None, f"{record['id']}: single form but a resonance note is set"


def test_no_duplicate_formula_charge_identity() -> None:
    seen: set[tuple[str, int]] = set()
    for record in RECORDS:
        key = (record["formula"], record["charge"])
        assert key not in seen, f"duplicate curated identity: {key}"
        seen.add(key)


def test_no_duplicate_curated_ids() -> None:
    ids = [record["id"] for record in RECORDS]
    assert len(ids) == len(set(ids))


# --------------------------------------------------------------------------- #
# Experimental geometry snapshot
# --------------------------------------------------------------------------- #

GEOMETRY_RECORDS = list(snapshot_records())


@pytest.mark.parametrize("evidence", GEOMETRY_RECORDS, ids=[r.id for r in GEOMETRY_RECORDS])
def test_experimental_geometry_identity_matches_a_curated_molecule(evidence: MolecularGeometryEvidence) -> None:
    curated_by_formula = {(r["formula"], r["charge"]): r for r in RECORDS}
    key = (evidence.identity.formula, evidence.identity.charge)
    assert key in curated_by_formula, f"{evidence.id}: no curated record for {key}"
    record = curated_by_formula[key]
    if evidence.identity.curated_molecule_id:
        assert evidence.identity.curated_molecule_id == record["id"]
    assert evidence.identity.atom_inventory == record["atom_inventory"]


@pytest.mark.parametrize("evidence", GEOMETRY_RECORDS, ids=[r.id for r in GEOMETRY_RECORDS])
def test_experimental_geometry_reproduces_its_own_observations(evidence: MolecularGeometryEvidence) -> None:
    fit = fit_cartesian_coordinates(evidence)
    assert fit.accepted, f"{evidence.id}: {fit.rejection_reason}"
    assert fit.max_length_deviation < 5e-3
    assert fit.max_angle_deviation < 2e-2


def test_no_duplicate_experimental_geometry_identity() -> None:
    seen: set[tuple[str, int]] = set()
    for evidence in GEOMETRY_RECORDS:
        key = (evidence.identity.formula, evidence.identity.charge)
        assert key not in seen, f"duplicate experimental geometry identity: {key}"
        seen.add(key)


# --------------------------------------------------------------------------- #
# Curated properties
# --------------------------------------------------------------------------- #

PROPERTY_CATALOG = curated_property_catalog()


@pytest.mark.parametrize("species_key", list(PROPERTY_CATALOG), ids=list(PROPERTY_CATALOG))
def test_curated_property_species_key_matches_a_curated_or_identity_species(species_key: str) -> None:
    formula, _, charge_str = species_key.rpartition("|")
    charge = int(charge_str)
    curated_formulas = {(r["formula"], r["charge"]) for r in RECORDS}
    assert (formula, charge) in curated_formulas, f"curated_properties.json has an entry for unknown species {species_key}"


@pytest.mark.parametrize("species_key", list(PROPERTY_CATALOG), ids=list(PROPERTY_CATALOG))
def test_no_duplicate_property_key_within_a_species(species_key: str) -> None:
    properties = PROPERTY_CATALOG[species_key]
    keys = [p.key for p in properties]
    assert len(keys) == len(set(keys)), f"{species_key}: duplicate property key(s) {keys}"


@pytest.mark.parametrize("species_key", list(PROPERTY_CATALOG), ids=list(PROPERTY_CATALOG))
def test_ion_species_never_carry_a_valued_bulk_property(species_key: str) -> None:
    """Bulk-phase properties on an isolated ion must be not_applicable, never a value."""

    _, _, charge_str = species_key.rpartition("|")
    charge = int(charge_str)
    if charge == 0:
        return
    bulk_keys = {"melting_point", "boiling_point", "density", "vapor_pressure", "solubility"}
    for item in PROPERTY_CATALOG[species_key]:
        if item.key in bulk_keys:
            assert item.applicability == "not_applicable", (
                f"{species_key}/{item.key}: bulk property on an ion must be not_applicable"
            )
            assert item.value is None


def test_every_curated_property_entry_is_a_valid_normalized_property() -> None:
    # Loading _catalog() already runs every entry through NormalizedProperty.model_validate;
    # reaching this point without an exception during collection is itself the proof, but
    # assert the catalog is non-empty so a loader regression can't silently pass by loading
    # zero records.
    assert sum(len(v) for v in PROPERTY_CATALOG.values()) > 0
