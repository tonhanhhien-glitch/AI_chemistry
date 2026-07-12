"""Focused API endpoint for strict formula parsing."""

from fastapi import APIRouter, HTTPException, Query

from app.core.exceptions import FormulaParseError
from app.schemas.formula_schema import FormulaParseResponse
from app.services.formula_parser import parse_formula

router = APIRouter()


@router.get("/formula", response_model=FormulaParseResponse)
def get_formula(
    formula: str = Query(..., description="Chemical formula, for example SO4^2-"),
) -> FormulaParseResponse:
    try:
        parsed = parse_formula(formula)
    except FormulaParseError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": exc.code, "message": exc.message},
        ) from exc

    return FormulaParseResponse(
        formula=parsed.formula,
        atoms=parsed.atoms,
        charge=parsed.charge,
    )
