"""Resolve only identities with curated or validated connectivity."""

from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.exceptions import AmbiguousMoleculeError, UnsupportedMoleculeError
from app.schemas.molecule_schema import MoleculeSummary, ResolvedMolecule
from app.services.formula_parser import ParsedFormula
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


def resolve_molecule(
    parsed: ParsedFormula, molecule_id: str | None = None
) -> tuple[ResolvedMolecule, dict[str, Any]]:
    if molecule_id:
        candidates = [get_record(molecule_id)]
    else:
        candidates = [r for r in curated_records() if r["formula"] == parsed.formula]
    if not candidates:
        raise UnsupportedMoleculeError(parsed.formula)
    if len(candidates) > 1:
        raise AmbiguousMoleculeError(
            [_summary(record).model_dump() for record in candidates]
        )
    record = candidates[0]
    if record["atom_inventory"] != parsed.atoms or record["charge"] != parsed.charge:
        raise UnsupportedMoleculeError(parsed.formula)
    resolved = ResolvedMolecule(
        **_summary(record).model_dump(),
        charge=record["charge"], atom_inventory=record["atom_inventory"],
        central_atom=record["central_atom"], source=record["source"],
        confidence=record["confidence"], pubchem_cid=record.get("pubchem_cid"),
        smiles=record.get("smiles"),
    )
    return resolved, record


def list_examples() -> list[MoleculeSummary]:
    return [_summary(record) for record in curated_records()]


def search_molecules(query: str) -> list[MoleculeSummary]:
    needle = query.strip().casefold()
    if not needle:
        return []
    matches = []
    for record in curated_records():
        haystack = [record["id"], record["formula"], record["name_vi"], record["name_en"], *record.get("aliases", [])]
        if any(needle in value.casefold() for value in haystack):
            matches.append(_summary(record))
    return matches[:20]
