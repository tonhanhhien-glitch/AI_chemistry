"""Models for the grounded molecule chat assistant."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

ChatLanguage = Literal["vi", "en"]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    molecule_id: str | None = Field(default=None, min_length=1, max_length=80)
    formula: str | None = Field(default=None, min_length=1, max_length=80)
    pubchem_cid: int | None = Field(default=None, gt=0)
    messages: list[ChatMessage] = Field(min_length=1, max_length=30)
    language: ChatLanguage = "vi"

    @model_validator(mode="after")
    def require_identity(self) -> "ChatRequest":
        if not self.molecule_id and not self.formula:
            raise ValueError("Either molecule_id or formula must be provided.")
        return self


class ChatResponse(BaseModel):
    reply: str
    source: Literal["claude", "deterministic_fallback"]
    fallback_reason: str | None = None
