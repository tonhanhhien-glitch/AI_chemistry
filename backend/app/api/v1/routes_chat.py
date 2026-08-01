"""POST /chat — grounded Q&A about one resolved molecule's immutable facts."""

from fastapi import APIRouter
from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.bond_angle_service import build_bond_angles
from app.services.chat_service import generate_chat_reply
from app.services.molecule_resolver import resolve_request_record
from app.services.structure3d_service import resolve_structure3d

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def post_chat(request: ChatRequest) -> ChatResponse:
    record = resolve_request_record(request.molecule_id, request.formula, request.pubchem_cid)
    structure = resolve_structure3d(record).structure
    record["_bond_angles"] = build_bond_angles(record, structure).model_dump()
    return generate_chat_reply(record, request.messages, request.language)
