"""Molecule Data admin CRUD/validate/preview/revert routes.

Every route in this router requires a valid admin session (see
``app/core/admin_auth.py``): the ``Depends(require_admin_session)`` below runs
before any handler body, so a missing/invalid session cookie 401s before any
molecule data is touched. The frontend's own route guard on ``/molecule-data``
is a UX convenience, not the security boundary -- this dependency is.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.admin_auth import require_admin_session
from app.schemas.molecule_admin import (
    CompletenessReport,
    DraftGenerationRequest,
    MoleculeAdminListResponse,
    MoleculeAdminRecord,
    MoleculeAdminSaveRequest,
    MoleculeAdminSaveResponse,
    ValidationReport,
)
from app.services import molecule_admin_service
from app.services.molecule_admin_service import MoleculeAdminNotFoundError, MoleculeValidationFailedError

router = APIRouter(dependencies=[Depends(require_admin_session)])


def _save(payload: MoleculeAdminSaveRequest) -> MoleculeAdminSaveResponse:
    try:
        return molecule_admin_service.save_molecule(payload)
    except MoleculeValidationFailedError as exc:
        # A literal 422 sidesteps the HTTP_422_UNPROCESSABLE_ENTITY/_CONTENT rename
        # across Starlette versions -- both still mean "well-formed but invalid".
        raise HTTPException(status_code=422, detail=exc.report.model_dump(mode="json")) from exc


# Literal-path routes are declared before the "/{molecule_id}" routes below so
# FastAPI never mistakes "export", "draft" or "preview" for a molecule id.


@router.get("/admin/molecules", response_model=MoleculeAdminListResponse)
def list_admin_molecules(q: str | None = Query(default=None, max_length=120)) -> MoleculeAdminListResponse:
    return MoleculeAdminListResponse(results=molecule_admin_service.list_molecules(q))


@router.get("/admin/molecules/export")
def export_admin_molecules() -> dict:
    return molecule_admin_service.export_catalog()


@router.post("/admin/molecules/draft")
def generate_admin_draft(payload: DraftGenerationRequest) -> dict:
    return molecule_admin_service.generate_draft(payload)


@router.post("/admin/molecules/preview")
def preview_admin_molecule(payload: MoleculeAdminSaveRequest):
    record = payload.molecule.model_dump(exclude_none=False)
    properties_override = list(payload.properties) if payload.properties else None
    return molecule_admin_service.preview_molecule(record, properties_override=properties_override)


@router.post("/admin/molecules", response_model=MoleculeAdminSaveResponse)
def create_admin_molecule(payload: MoleculeAdminSaveRequest) -> MoleculeAdminSaveResponse:
    return _save(payload)


@router.get("/admin/molecules/{molecule_id}", response_model=MoleculeAdminRecord)
def get_admin_molecule(molecule_id: str) -> MoleculeAdminRecord:
    try:
        return molecule_admin_service.get_molecule(molecule_id)
    except MoleculeAdminNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/admin/molecules/{molecule_id}", response_model=MoleculeAdminSaveResponse)
def update_admin_molecule(molecule_id: str, payload: MoleculeAdminSaveRequest) -> MoleculeAdminSaveResponse:
    payload.molecule.id = molecule_id
    return _save(payload)


@router.post("/admin/molecules/{molecule_id}/validate", response_model=ValidationReport)
def validate_admin_molecule(molecule_id: str, payload: MoleculeAdminSaveRequest) -> ValidationReport:
    payload.molecule.id = molecule_id
    record = payload.molecule.model_dump(exclude_none=False)
    return molecule_admin_service.validate_molecule(
        record, geometry=payload.experimental_geometry, properties=list(payload.properties)
    )


@router.post("/admin/molecules/{molecule_id}/revert")
def revert_admin_molecule(molecule_id: str) -> dict:
    return molecule_admin_service.revert_molecule(molecule_id)


@router.get("/admin/molecules/{molecule_id}/completeness", response_model=CompletenessReport)
def get_admin_completeness(molecule_id: str) -> CompletenessReport:
    try:
        return molecule_admin_service.completeness_report(molecule_id)
    except MoleculeAdminNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
