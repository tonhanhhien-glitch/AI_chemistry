"""Response models for formula parsing."""

from pydantic import BaseModel


class FormulaParseResponse(BaseModel):
    formula: str
    atoms: dict[str, int]
    charge: int
