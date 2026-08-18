"""CRUD, validation and preview for admin-edited molecule records.

Overrides are stored as one JSON document (see ``molecule_overrides.py``) at
``DATA_DIR/molecule_catalog_overrides.json``. Every write is atomic. After
every save/revert the baseline ``@lru_cache`` loaders admin edits can affect
are cleared, so ``/api/v1/analyze`` and every other read path see the new
effective catalog on the very next request -- no backend restart needed.

Validation and preview deliberately reuse the same deterministic chemistry
services the live ``/analyze`` pipeline uses (``lewis_service``,
``vsepr_engine``, ``structure3d_service``, ``bond_angle_service``,
``property_service``) so the admin page can never drift from what a student
actually sees.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.exceptions import ChemistryValidationError
from app.geometry.providers import nist_cccbdb
from app.properties.providers.base import PropertyQuery
from app.properties.providers.curated import CuratedPropertyProvider
from app.properties.providers import curated as curated_properties_provider
from app.properties.schema import NormalizedProperty
from app.schemas.analysis_schema import AnalysisNotices, AnalysisResponse
from app.schemas.geometry_evidence_schema import MolecularGeometryEvidence
from app.schemas.molecule_admin import (
    CompletenessReport,
    DraftGenerationRequest,
    MoleculeAdminListItem,
    MoleculeAdminRecord,
    MoleculeAdminSaveRequest,
    MoleculeAdminSaveResponse,
    MoleculeDraft,
    ValidationIssue,
    ValidationReport,
)
from app.services import molecule_overrides, molecule_resolver
from app.services.bond_angle_service import build_bond_angles
from app.services.deterministic_chemistry_service import build_deterministic_record
from app.services.experimental_geometry_service import match_experimental_geometry
from app.services.formula_parser import ParsedFormula, canonical_formula, parse_formula
from app.services.lewis_service import build_lewis_structure
from app.services.property_service import get_properties
from app.services.structure3d_service import resolve_structure3d
from app.services.vsepr_engine import analyze_vsepr

_BASELINE_MOLECULES_FILE = Path(__file__).resolve().parents[1] / "data" / "curated_molecules.json"


class MoleculeAdminNotFoundError(Exception):
    def __init__(self, molecule_id: str) -> None:
        super().__init__(f"No such molecule: {molecule_id}")
        self.molecule_id = molecule_id


class MoleculeValidationFailedError(Exception):
    """Raised by save_molecule() when validation errors must block the save."""

    def __init__(self, report: ValidationReport) -> None:
        super().__init__("Molecule failed validation; not saved.")
        self.report = report


def reload_effective_catalog() -> None:
    """Clear every cache an admin edit can invalidate. Safe to call any time."""

    molecule_resolver.curated_records.cache_clear()
    nist_cccbdb.snapshot_records.cache_clear()
    curated_properties_provider._catalog.cache_clear()  # noqa: SLF001 - intentional cache reset


def _baseline_molecule_ids() -> set[str]:
    from app.utils.file_loader import load_json

    data = load_json(_BASELINE_MOLECULES_FILE)
    return {item["id"] for item in data.get("molecules", [])}


def _species_key(record: dict[str, Any]) -> str:
    return f"{record.get('formula', '')}|{int(record.get('charge', 0))}"


def _curated_properties(record: dict[str, Any]) -> list[NormalizedProperty]:
    query = PropertyQuery.from_record(record)
    return list(CuratedPropertyProvider().fetch(query).properties)


def _list_item(record: dict[str, Any], *, override_ids: set[str], baseline_ids: set[str]) -> MoleculeAdminListItem:
    record_id = record["id"]
    return MoleculeAdminListItem(
        id=record_id,
        formula=record.get("formula", ""),
        charge=int(record.get("charge", 0)),
        name_vi=record.get("name_vi", ""),
        name_en=record.get("name_en", ""),
        ax_en=record.get("ax_en", ""),
        molecular_geometry=record.get("molecular_geometry", ""),
        molecular_geometry_vi=record.get("molecular_geometry_vi", ""),
        review_status=record.get("review_status", ""),
        has_override=record_id in override_ids,
        is_admin_added=record_id in override_ids and record_id not in baseline_ids,
    )


def list_molecules(query: str | None = None) -> list[MoleculeAdminListItem]:
    overrides = molecule_overrides.load_overrides()
    override_ids = {item["id"] for item in overrides.get("molecules", []) if "id" in item}
    baseline_ids = _baseline_molecule_ids()
    needle = (query or "").strip().casefold()
    items: list[MoleculeAdminListItem] = []
    for record in molecule_resolver.curated_records():
        if needle:
            haystack = [
                record.get("id", ""), record.get("formula", ""),
                record.get("name_vi", ""), record.get("name_en", ""),
                *(record.get("aliases") or []),
                str(record.get("cas_rn") or ""), str(record.get("pubchem_cid") or ""),
            ]
            if not any(needle in str(value).casefold() for value in haystack):
                continue
        items.append(_list_item(record, override_ids=override_ids, baseline_ids=baseline_ids))
    return items


def get_molecule(molecule_id: str) -> MoleculeAdminRecord:
    try:
        record = molecule_resolver.get_record(molecule_id)
    except Exception as exc:  # UnsupportedMoleculeError from molecule_resolver
        raise MoleculeAdminNotFoundError(molecule_id) from exc
    overrides = molecule_overrides.load_overrides()
    override_ids = {item["id"] for item in overrides.get("molecules", []) if "id" in item}
    baseline_ids = _baseline_molecule_ids()
    return MoleculeAdminRecord(
        molecule=record,
        experimental_geometry=match_experimental_geometry(record),
        properties=_curated_properties(record),
        has_override=molecule_id in override_ids,
        is_admin_added=molecule_id in override_ids and molecule_id not in baseline_ids,
    )


def generate_draft(payload: DraftGenerationRequest) -> dict[str, Any]:
    """Deterministic-engine draft for "+ Add Molecule -> Generate deterministic draft".

    Returns a record dict shaped exactly like a curated molecule entry; the caller
    still has to Save it for the draft to become persistent.
    """

    bare = parse_formula(payload.formula)
    parsed = ParsedFormula(formula=canonical_formula(bare.atoms, payload.charge), atoms=bare.atoms, charge=payload.charge)
    record = build_deterministic_record(parsed)
    record.pop("_connectivity_source", None)
    if payload.id:
        record["id"] = payload.id
    if payload.name_vi:
        record["name_vi"] = payload.name_vi
    if payload.name_en:
        record["name_en"] = payload.name_en
    return record


def _upsert(items: list[dict[str, Any]], item: dict[str, Any], *, key: str) -> None:
    for index, existing in enumerate(items):
        if existing.get(key) == item.get(key):
            items[index] = item
            return
    items.append(item)


def validate_molecule(
    record: dict[str, Any],
    *,
    geometry: MolecularGeometryEvidence | None = None,
    properties: list[NormalizedProperty] | None = None,
) -> ValidationReport:
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
    info: list[ValidationIssue] = []

    def err(field: str, vi: str, en: str) -> None:
        errors.append(ValidationIssue(severity="error", field=field, message_vi=vi, message_en=en))

    def warn(field: str, vi: str, en: str) -> None:
        warnings.append(ValidationIssue(severity="warning", field=field, message_vi=vi, message_en=en))

    def note(field: str, vi: str, en: str) -> None:
        info.append(ValidationIssue(severity="info", field=field, message_vi=vi, message_en=en))

    formula = str(record.get("formula", ""))
    charge = int(record.get("charge", 0))
    inventory = record.get("atom_inventory") or {}

    try:
        parsed = parse_formula(formula)
        if parsed.atoms != inventory:
            err("atom_inventory", "Kiểm kê nguyên tử không khớp với công thức.",
                "Atom inventory does not match the formula.")
        if parsed.charge and parsed.charge != charge and formula.strip().endswith(("+", "-")):
            warn("charge", "Điện tích trong công thức khác với trường điện tích.",
                 "The charge embedded in the formula differs from the charge field.")
    except Exception as exc:  # noqa: BLE001 - collect every problem, do not fail fast
        err("formula", f"Công thức không hợp lệ: {exc}", f"Invalid formula: {exc}")

    if len(record.get("atom_symbols") or []) != sum(inventory.values()):
        err("atom_symbols", "Số ký hiệu nguyên tử không khớp kiểm kê nguyên tử.",
            "Atom symbol count does not match the atom inventory total.")

    try:
        build_lewis_structure(record)
    except ChemistryValidationError as exc:
        err("lewis", str(exc), str(exc))
    except Exception as exc:  # noqa: BLE001
        err("lewis", f"Lỗi cấu trúc Lewis: {exc}", f"Lewis structure error: {exc}")

    try:
        analyze_vsepr(record)
    except ChemistryValidationError as exc:
        err("vsepr", str(exc), str(exc))
    except Exception as exc:  # noqa: BLE001
        err("vsepr", f"Lỗi VSEPR: {exc}", f"VSEPR error: {exc}")

    bonding = int(record.get("bonding_domains", 0))
    lone = int(record.get("lone_pair_domains", 0))
    steric = record.get("steric_number")
    if steric is not None and bonding + lone != int(steric):
        err("steric_number", "Số lập thể phải bằng tổng miền liên kết và miền cặp riêng.",
            "Steric number must equal bonding domains plus lone-pair domains.")

    self_id = record.get("id")
    duplicates = [
        other for other in molecule_resolver.curated_records()
        if other.get("id") != self_id and other.get("formula") == formula and int(other.get("charge", 0)) == charge
    ]
    if duplicates:
        err("formula", f"Đã có phân tử khác với công thức {formula} và điện tích {charge} ({duplicates[0].get('id')}).",
            f"Another molecule already has formula {formula} and charge {charge} ({duplicates[0].get('id')}).")

    if geometry is not None:
        if geometry.identity.formula and geometry.identity.formula != formula:
            warn("experimental_geometry", "Công thức trong dữ liệu thực nghiệm khác công thức phân tử.",
                 "The experimental-geometry record's formula differs from the molecule's formula.")
        if geometry.identity.charge != charge:
            warn("experimental_geometry", "Điện tích trong dữ liệu thực nghiệm khác điện tích phân tử.",
                 "The experimental-geometry record's charge differs from the molecule's charge.")

    if not record.get("teaching_note_vi") and not record.get("teaching_note_en"):
        note("teaching_note", "Chưa có ghi chú giảng dạy chung.", "No general teaching note yet.")
    if not properties:
        note("properties", "Chưa có tính chất được tuyển chọn cho chất này.", "No curated properties for this species yet.")
    if record.get("review_status") == "expert_verified":
        warn("review_status", "Đang lưu ở trạng thái đã thẩm định chuyên gia -- hãy chắc chắn điều này đúng.",
             "Saving with review_status=expert_verified -- make sure that is actually true.")

    return ValidationReport(is_valid=not errors, errors=errors, warnings=warnings, info=info)


def preview_molecule(
    record: dict[str, Any],
    properties_override: list[NormalizedProperty] | None = None,
) -> AnalysisResponse:
    """Run the same pipeline ``/analyze`` uses, directly on an unsaved draft.

    Reflects the currently *saved* experimental geometry (if any) for this
    identity -- an unsaved experimental-geometry edit in the same editing
    session appears here only after Save, since geometry resolution reads the
    catalog rather than accepting an ad hoc override.
    """

    molecule = molecule_resolver._resolved(dict(record))  # noqa: SLF001 - shared summary builder
    lewis = build_lewis_structure(record)
    vsepr = analyze_vsepr(record)
    structure_result = resolve_structure3d(record)
    bond_angles = build_bond_angles(record, structure_result.structure)
    properties = properties_override if properties_override is not None else get_properties(record)

    warnings_vi = [structure_result.structure.warning_vi] if structure_result.structure.warning_vi else []
    warnings_en = [structure_result.structure.warning_en] if structure_result.structure.warning_en else []
    warnings_vi.append("Đây là bản xem trước cho bản nháp chưa lưu.")
    warnings_en.append("This is a preview of an unsaved draft.")

    return AnalysisResponse(
        molecule=molecule,
        lewis=lewis,
        vsepr=vsepr,
        properties=properties,
        structure3d=structure_result.structure,
        bond_angles=bond_angles,
        explanation=None,
        notices=AnalysisNotices(
            offline_capable=record.get("source") != "PubChem reference",
            external_services_used=[],
            warnings_vi=warnings_vi,
            warnings_en=warnings_en,
            external_service_statuses=list(structure_result.statuses),
        ),
    )


def save_molecule(payload: MoleculeAdminSaveRequest) -> MoleculeAdminSaveResponse:
    record = payload.molecule.model_dump(exclude_none=False)
    properties = list(payload.properties)
    validation = validate_molecule(record, geometry=payload.experimental_geometry, properties=properties)
    if not validation.is_valid:
        raise MoleculeValidationFailedError(validation)

    overrides = molecule_overrides.load_overrides()
    _upsert(overrides["molecules"], record, key="id")

    if payload.experimental_geometry is not None:
        geometry_dict = payload.experimental_geometry.model_dump(mode="json")
        geometry_dict["id"] = f"admin-{record['id']}"
        geometry_dict.setdefault("identity", {})
        geometry_dict["identity"]["curated_molecule_id"] = record["id"]
        geometry_dict["identity"].setdefault("formula", record.get("formula", ""))
        geometry_dict["identity"].setdefault("charge", int(record.get("charge", 0)))
        _upsert(overrides["experimental_geometries"], geometry_dict, key="id")

    if properties:
        overrides["properties"][_species_key(record)] = [item.model_dump(mode="json") for item in properties]

    molecule_overrides.save_overrides(overrides)
    reload_effective_catalog()

    override_ids = {item["id"] for item in overrides["molecules"] if "id" in item}
    return MoleculeAdminSaveResponse(
        molecule=_list_item(record, override_ids=override_ids, baseline_ids=_baseline_molecule_ids()),
        validation=validation,
        saved_at=datetime.now(UTC),
    )


def revert_molecule(molecule_id: str) -> dict[str, bool]:
    species_key: str | None = None
    try:
        current = molecule_resolver.get_record(molecule_id)
        species_key = _species_key(current)
    except Exception:  # noqa: BLE001 - nothing to key properties removal by
        pass

    overrides = molecule_overrides.load_overrides()
    had_override = any(item.get("id") == molecule_id for item in overrides["molecules"])
    overrides["molecules"] = [item for item in overrides["molecules"] if item.get("id") != molecule_id]
    geometry_override_id = f"admin-{molecule_id}"
    overrides["experimental_geometries"] = [
        item for item in overrides["experimental_geometries"] if item.get("id") != geometry_override_id
    ]
    if species_key is not None:
        overrides["properties"].pop(species_key, None)

    molecule_overrides.save_overrides(overrides)
    reload_effective_catalog()

    baseline_ids = _baseline_molecule_ids()
    return {"had_override": had_override, "reverted_to_baseline": molecule_id in baseline_ids}


def completeness_report(molecule_id: str) -> CompletenessReport:
    admin_record = get_molecule(molecule_id)
    record = admin_record.molecule
    required_fields = [
        "name_vi", "name_en", "smiles", "inchi", "inchikey", "teaching_note_vi", "teaching_note_en",
        "polarity_note_vi", "polarity_note_en", "distortion_note_vi", "distortion_note_en",
    ]
    missing = [field for field in required_fields if not record.get(field)]
    if admin_record.experimental_geometry is None:
        missing.append("experimental_geometry")
    if not admin_record.properties:
        missing.append("properties")
    total_checks = len(required_fields) + 2
    completeness_percent = round(100.0 * (total_checks - len(missing)) / total_checks, 1)
    return CompletenessReport(
        molecule_id=molecule_id,
        missing_fields=missing,
        has_experimental_geometry=admin_record.experimental_geometry is not None,
        has_properties=bool(admin_record.properties),
        review_status=str(record.get("review_status", "")),
        completeness_percent=completeness_percent,
    )


def export_catalog() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "molecules": list(molecule_resolver.curated_records()),
        "experimental_geometries": [item.model_dump(mode="json") for item in nist_cccbdb.snapshot_records()],
    }
