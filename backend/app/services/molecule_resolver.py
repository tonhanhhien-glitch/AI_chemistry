"""Resolve curated identities first, then validated PubChem candidates."""

from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.exceptions import (
    AmbiguousMoleculeError,
    ChemistryValidationError,
    ExternalResolutionError,
    UnsupportedMoleculeError,
)
from app.schemas.molecule_schema import (
    Connectivity, ConnectivityAtom, ConnectivityBond, ExternalServiceState,
    MoleculeSummary,
    PubChemCandidate,
    ResolvedMolecule,
)
from app.services.chemical_query_resolver import cas_for_identity, local_identities
from app.services.deterministic_chemistry_service import build_deterministic_record
from app.services.formula_parser import ParsedFormula, parse_formula
from app.services.pubchem_service import lookup_pubchem_formula
from app.utils.file_loader import load_json

_DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "curated_molecules.json"


@lru_cache(maxsize=1)
def curated_records() -> tuple[dict[str, Any], ...]:
    data = load_json(_DATA_FILE)
    records = data.get("molecules")
    if not isinstance(records, list):
        raise ValueError("curated_molecules.json must contain a molecules list")
    return tuple(records)


def _summary(record: dict[str, Any]) -> MoleculeSummary:
    return MoleculeSummary(
        id=record["id"], formula=record["formula"], name_vi=record["name_vi"],
        name_en=record["name_en"], ax_en=record["ax_en"],
        molecular_geometry=record["molecular_geometry"],
        molecular_geometry_vi=record["molecular_geometry_vi"],
        review_status=record["review_status"],
    )


def get_record(molecule_id: str) -> dict[str, Any]:
    normalized = molecule_id.strip().casefold()
    for record in curated_records():
        if record["id"].casefold() == normalized:
            return record
    raise UnsupportedMoleculeError(molecule_id)


def _with_registry_identifiers(record: dict[str, Any]) -> dict[str, Any]:
    """Attach the local CAS registry number so geometry providers can address the species.

    CCCBDB is keyed on CAS, so without this a live experimental lookup has no address.
    An unknown formula simply gets ``None`` and the live provider reports a typed miss.
    """

    if record.get("cas_rn") is None:
        record["cas_rn"] = cas_for_identity(record["formula"], int(record["charge"]))
    return record


def _resolved(record: dict[str, Any]) -> ResolvedMolecule:
    return ResolvedMolecule(
        **_summary(record).model_dump(),
        charge=record["charge"],
        atom_inventory=record["atom_inventory"],
        central_atom=record["central_atom"],
        source=record["source"],
        confidence=record["confidence"],
        pubchem_cid=record.get("pubchem_cid"),
        smiles=record.get("smiles"),
        canonical_identity=record.get("canonical_identity"),
        inchi=record.get("inchi"),
        inchikey=record.get("inchikey"),
        validation_status=record.get("validation_status", "curated_verified"),
        cache_timestamp=record.get("cache_timestamp"),
        connectivity=Connectivity(
            atoms=[ConnectivityAtom(id=f"a{index}", element=symbol) for index, symbol in enumerate(record["atom_symbols"])],
            bonds=[ConnectivityBond(atom1_id="a0", atom2_id=f"a{index + 1}", order=order) for index, order in enumerate(record["bond_orders"])],
            central_atom_id="a0",
        ),
    )


def _candidate_summary(candidate: PubChemCandidate, record: dict[str, Any]) -> dict[str, object]:
    return {
        **candidate.model_dump(mode="json"),
        "ax_en": record["ax_en"],
        "molecular_geometry": record["molecular_geometry"],
        "molecular_geometry_vi": record["molecular_geometry_vi"],
    }


def resolve_molecule(
    parsed: ParsedFormula,
    molecule_id: str | None = None,
    pubchem_cid: int | None = None,
    candidate: PubChemCandidate | None = None,
) -> tuple[ResolvedMolecule, dict[str, Any]]:
    """Resolve in curated -> PubChem -> conservative deterministic priority order.

    ``candidate`` is an identity the query resolver has already validated. Passing it
    here skips a second PubChem round-trip for a lookup that has just been made.
    """

    if molecule_id:
        record = _with_registry_identifiers(get_record(molecule_id))
        if record["atom_inventory"] != parsed.atoms or record["charge"] != parsed.charge:
            raise UnsupportedMoleculeError(parsed.formula)
        return _resolved(record), record

    curated = [record for record in curated_records() if record["formula"] == parsed.formula]
    if len(curated) > 1:
        raise AmbiguousMoleculeError([_summary(record).model_dump() for record in curated])
    if len(curated) == 1:
        record = _with_registry_identifiers(curated[0])
        if record["atom_inventory"] != parsed.atoms or record["charge"] != parsed.charge:
            raise UnsupportedMoleculeError(parsed.formula)
        return _resolved(record), record

    if candidate is not None:
        record = _with_registry_identifiers(build_deterministic_record(parsed, candidate))
        return _resolved(record), record

    lookup = lookup_pubchem_formula(parsed)
    if not lookup.candidates:
        fallback_states = {ExternalServiceState.DISABLED, ExternalServiceState.NOT_FOUND, ExternalServiceState.FORMULA_MISMATCH}
        if pubchem_cid is not None or lookup.status.state not in fallback_states:
            raise ExternalResolutionError(parsed.formula, lookup.status.state.value)
        try:
            record = build_deterministic_record(parsed)
        except ChemistryValidationError:
            if lookup.status.state is ExternalServiceState.DISABLED:
                raise UnsupportedMoleculeError(parsed.formula) from None
            raise ExternalResolutionError(parsed.formula, lookup.status.state.value) from None
        record["_external_service_statuses"] = [lookup.status]
        _with_registry_identifiers(record)
        return _resolved(record), record

    candidates = lookup.candidates
    if pubchem_cid is not None:
        candidates = [candidate for candidate in candidates if candidate.cid == pubchem_cid]
        if not candidates:
            raise UnsupportedMoleculeError(f"{parsed.formula} / PubChem CID {pubchem_cid}")

    valid: list[tuple[PubChemCandidate, dict[str, Any]]] = []
    for candidate in candidates:
        try:
            valid.append((candidate, build_deterministic_record(parsed, candidate)))
        except ChemistryValidationError:
            continue
    if not valid:
        raise UnsupportedMoleculeError(parsed.formula)
    if len(valid) > 1:
        raise AmbiguousMoleculeError([_candidate_summary(candidate, record) for candidate, record in valid])

    candidate, record = valid[0]
    record["_external_service_statuses"] = [lookup.status]
    _with_registry_identifiers(record)
    return _resolved(record), record


def resolve_request_record(molecule_id: str | None, formula: str | None, pubchem_cid: int | None = None) -> dict[str, Any]:
    if molecule_id and not molecule_id.startswith(("deterministic:", "pubchem:")):
        return get_record(molecule_id)
    if formula:
        _molecule, record = resolve_molecule(parse_formula(formula), None, pubchem_cid)
        return record
    if molecule_id:
        return get_record(molecule_id)
    raise UnsupportedMoleculeError("missing identity")


def list_examples() -> list[MoleculeSummary]:
    return [_summary(record) for record in curated_records()]


def search_molecules(query: str) -> list[MoleculeSummary]:
    """Search curated records first, then the wider local identity registry.

    Search is no longer limited to ``curated_records()``: a name that only exists in
    the identity registry still appears, marked as pending deterministic analysis so
    the UI never implies a reviewed VSEPR classification it does not have.
    """

    needle = query.strip().casefold()
    if not needle:
        return []
    matches = []
    seen_formulas: set[tuple[str, int]] = set()
    for record in curated_records():
        haystack = [record["id"], record["formula"], record["name_vi"], record["name_en"], *record.get("aliases", [])]
        if any(needle in value.casefold() for value in haystack):
            matches.append(_summary(record))
            seen_formulas.add((record["formula"], int(record["charge"])))
    for identity in local_identities():
        key = (identity.formula, identity.charge)
        if key in seen_formulas:
            continue
        if identity.formula.casefold() == needle or any(needle in name.casefold() for name in identity.names):
            seen_formulas.add(key)
            matches.append(MoleculeSummary(
                id=identity.curated_molecule_id or f"formula:{identity.formula}",
                formula=identity.formula,
                name_vi=identity.names[0] if identity.names else identity.formula,
                name_en=identity.names[0] if identity.names else identity.formula,
                ax_en="pending",
                molecular_geometry="pending deterministic analysis",
                molecular_geometry_vi="đang chờ phân tích tất định",
                review_status="identity_registry_pending_analysis",
            ))
    return matches[:20]
