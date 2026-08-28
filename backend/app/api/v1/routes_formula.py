from fastapi import APIRouter, HTTPException, Query

from backend.app.services.formula_parser import parse_formula
from backend.app.services.lewis_service import analyze_formula as analyze_lewis

router = APIRouter()


def guess_central_atom(atoms: dict[str, int]) -> str:
    """
    Chọn nguyên tử trung tâm cho các phân tử vô cơ nhóm chính.
    """

    non_h = [atom for atom in atoms if atom != "H"]

    if not non_h:
        return "H"

    if len(non_h) == 1:
        return non_h[0]

    priority = [
        "C",
        "N",
        "P",
        "S",
        "B",
        "Si",
        "O",
        "Cl",
        "Br",
        "I",
        "F",
    ]

    for element in priority:
        if element in non_h:
            return element

    return non_h[0]


@router.get("/analyze")
def analyze_formula_route(
    formula: str = Query(..., description="Chemical formula, ví dụ: H2O"),
):
    try:
        parsed = parse_formula(formula)

        central = guess_central_atom(parsed.atoms)

        result = analyze_lewis(
            atoms=parsed.atoms,
            central_atom=central,
            charge=parsed.charge,
        )

        return {
            "success": True,
            "data": result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))