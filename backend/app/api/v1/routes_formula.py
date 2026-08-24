from fastapi import APIRouter, Query

from backend.app.core.exceptions import FormulaParseError
from backend.app.schemas.formula_schema import FormulaParseResponse
from backend.app.services.formula_parser import parse_formula

from chemistry.molecular_engine import analyze_molecule

router = APIRouter()


@router.get("/formula/parse", response_model=FormulaParseResponse)
def parse_formula_endpoint(
    formula: str = Query(..., description="Ví dụ: H2O, NH3, SO4^2-")
):
    try:
        parsed = parse_formula(formula)

        return FormulaParseResponse(
            success=True,
            data=parsed
        )

    except FormulaParseError as e:
        return FormulaParseResponse(
            success=False,
            error={
                "code": e.code,
                "message": e.message
            }
        )


@router.get("/analyze")
def analyze_formula(
    formula: str = Query(..., description="Chemical formula")
):
    parsed = parse_formula(formula)

    result = analyze_molecule(
        atoms=parsed["atoms"],
        central_atom=parsed["central_atom"],
        charge=parsed["charge"]
    )

    return {
        "success": True,
        "data": result
    }