import re


def extract_charge(formula: str):

    charge = 0

    match = re.search(r"\^(\d+)([+-])$", formula)

    if match:

        number = int(match.group(1))
        sign = match.group(2)

        charge = number if sign == "+" else -number

        formula = re.sub(r"\^\d+[+-]$", "", formula)

    elif formula.endswith("+"):

        charge = 1
        formula = formula[:-1]

    elif formula.endswith("-"):

        charge = -1
        formula = formula[:-1]

    return formula, charge


def extract_atoms(formula: str):

    matches = re.findall(
        r"([A-Z][a-z]?)(\d*)",
        formula
    )

    atoms = {}

    for symbol, count in matches:

        atoms[symbol] = int(count) if count else 1

    return atoms


def parse(formula: str):

    formula, charge = extract_charge(formula)

    atoms = extract_atoms(formula)

    return {
        "formula": formula,
        "atoms": atoms,
        "charge": charge
    }


if __name__ == "__main__":

    examples = [
        "H2O",
        "CO2",
        "NH3",
        "H2SO4",
        "NH4+",
        "NO3-",
        "SO4^2-",
        "PO4^3-"
    ]

    for formula in examples:

        print(parse(formula))