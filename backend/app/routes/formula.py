from fastapi import APIRouter, HTTPException
from backend.app.services.formula_parser import parse_formula

router = APIRouter()

@router.get("/analyze")
def analyze_formula(formula: str):
    try:
        result = parse_formula(formula)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    