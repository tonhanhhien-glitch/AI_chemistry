from chemistry.periodic_table import PERIODIC_TABLE


NEVER_CENTER = {
    "H",
    "F",
    "Cl",
    "Br",
    "I"
}


def choose_central_atom(atoms: dict):

    candidates = []

    for atom in atoms:

        if atom not in NEVER_CENTER:

            candidates.append(atom)

    if len(candidates) == 1:

        return candidates[0]

    lowest = None

    lowest_value = 100

    for atom in candidates:

        value = PERIODIC_TABLE[atom]["electronegativity"]

        if value < lowest_value:

            lowest = atom
            lowest_value = value

    return lowest


if __name__ == "__main__":

    examples = [

        {"C":1,"O":2},

        {"N":1,"H":3},

        {"O":1,"H":2},

        {"S":1,"O":4},

        {"P":1,"Cl":5}

    ]

    for atoms in examples:

        print(atoms)

        print(
            choose_central_atom(atoms)
        )

        print()