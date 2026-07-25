"""Models for the grounded molecule chat assistant."""

from typing import Literal

from pydantic import BaseModel, Field

ChatLanguage = Literal["vi", "en"]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    molecule_id: str = Field(min_length=1, max_length=80)
    messages: list[ChatMessage] = Field(min_length=1, max_length=30)
    language: ChatLanguage = "vi"


class ChatResponse(BaseModel):
    reply: str
    source: Literal["claude", "deterministic_fallback"]
    fallback_reason: str | None = None
