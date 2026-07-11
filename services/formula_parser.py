import re

# Danh sách nguyên tố hỗ trợ (tạm thời)
SUPPORTED_ELEMENTS = {
    "H", "He",
    "Li", "Be", "B", "C", "N", "O", "F", "Ne",
    "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar",
    "K", "Ca",
    "Br", "I", "Xe"
}


def parse_formula(formula: str):

    formula = formula.strip()

    if formula == "":
        return {
            "success": False,
            "error": "Công thức hóa học không được để trống."
        }

    charge = 0

    charge_match = re.search(r"\^(\d+)([+-])$", formula)

    if charge_match:
        number = int(charge_match.group(1))
        sign = charge_match.group(2)

        charge = number if sign == "+" else -number

        formula = re.sub(r"\^\d+[+-]$", "", formula)

    elif formula.endswith("+"):
        charge = 1
        formula = formula[:-1]

    elif formula.endswith("-"):
        charge = -1
        formula = formula[:-1]

    if not re.fullmatch(r"[A-Za-z0-9]+", formula):
        return {
            "success": False,
            "error": "Công thức chứa ký tự không hợp lệ."
        }

    formula = formula.upper()

    matches = re.findall(r"([A-Z][a-z]?)(\d*)", formula)

    atoms = {}

    for element, number in matches:

        if element not in SUPPORTED_ELEMENTS:
            return {
                "success": False,
                "error": f"Nguyên tố '{element}' hiện chưa được hỗ trợ."
            }

        atoms[element] = int(number) if number else 1

    return {
        "success": True,
        "formula": formula,
        "atoms": atoms,
        "charge": charge
    }