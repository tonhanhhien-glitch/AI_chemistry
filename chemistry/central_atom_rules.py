# chemistry/central_atom_rules.py

NEVER_CENTRAL = {
    "H",
    "F",
    "Cl",
    "Br",
    "I"
}

def is_possible_central(symbol: str):

    return symbol not in NEVER_CENTRAL

if __name__ == "__main__":

    print(is_possible_central("H"))
    print(is_possible_central("O"))
    print(is_possible_central("Cl"))
    print(is_possible_central("C"))