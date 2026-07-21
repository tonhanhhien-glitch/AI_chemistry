from chemistry.periodic_table import get_valence
from chemistry.formula_parser import parse


def calculate_element_valence(symbol: str, count: int):

    valence = get_valence(symbol)

    return valence * count


def calculate_total_valence(atoms: dict):

    total = 0

    for symbol, count in atoms.items():

        total += calculate_element_valence(symbol, count)

    return total


def calculate_total_valence_with_charge(formula: str):

    result = parse(formula)

    atoms = result["atoms"]
    charge = result["charge"]

    total = calculate_total_valence(atoms)

    if charge > 0:
        total -= charge

    elif charge < 0:
        total += abs(charge)

    return {
        "formula": formula,
        "atoms": atoms,
        "charge": charge,
        "total_valence": total
    }


if __name__ == "__main__":

    examples = [

        "H2O",
        "CO2",
        "NH3",
        "NH4+",
        "NO3-",
        "SO4^2-",
        "PO4^3-"

    ]

    for formula in examples:

        print(calculate_total_valence_with_charge(formula))