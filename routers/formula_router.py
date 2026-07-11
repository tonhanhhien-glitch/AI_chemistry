from fastapi import APIRouter

from services.formula_parser import parse_formula

router = APIRouter()


@router.get("/formula")
def formula(formula: str):
    return parse_formula(formula)