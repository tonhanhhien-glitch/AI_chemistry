"""POST /properties -- lazily loaded physical and chemical properties.

Kept off ``/analyze`` on purpose: the deterministic parsing, Lewis, VSEPR and cached
geometry stages must stay fast, so the several external requests needed for a full
property table only happen when the student actually opens the property section.
"""

from fastapi import APIRouter

from app.properties.schema import PropertyBundle
from app.schemas.analysis_schema import PropertyRequest
from app.services.molecule_resolver import resolve_request_record
from app.services.property_service import get_property_bundle

router = APIRouter()


@router.post("/properties", response_model=PropertyBundle)
def post_properties(request: PropertyRequest) -> PropertyBundle:
    record = resolve_request_record(request.molecule_id, request.formula, request.pubchem_cid)
    return get_property_bundle(record)
