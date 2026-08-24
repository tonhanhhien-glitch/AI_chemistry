"""Pydantic models for the /analyze request and its full aggregated response."""
from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    atoms: dict
    central_atom: str
    charge: int = 0


class AnalyzeResponse(BaseModel):
    success: bool
    data: dict

from typing import Any


class AnalyzeResponse(BaseModel):
    success: bool
    data: dict[str, Any]