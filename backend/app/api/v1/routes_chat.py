"""POST /chat — grounded Q&A about one curated molecule's immutable facts."""

from fastapi import APIRouter

from app.schemas.chat_schema import ChatRequest, ChatResponse
from app.services.chat_service import generate_chat_reply
from app.services.molecule_resolver import get_record

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def post_chat(request: ChatRequest) -> ChatResponse:
    return generate_chat_reply(get_record(request.molecule_id), request.messages, request.language)
