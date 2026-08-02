from chemistry.periodic_table import get_electronegativity


NEVER_CENTER = {
    "H",
    "F",
    "Cl",
    "Br",
    "I"
}


def get_candidates(atoms: dict):

    return list(atoms.keys())


def remove_terminal_atoms(candidates: list):

    return [

        atom

        for atom in candidates

        if atom not in NEVER_CENTER

    ]


def choose_if_only_one(candidates: list):

    if len(candidates) == 1:

        return candidates[0]

    return None


def compare_electronegativity(candidates: list):

    lowest = None

    lowest_value = float("inf")

    for atom in candidates:

        value = get_electronegativity(atom)

        if value is None:
            continue

        if value < lowest_value:

            lowest = atom
            lowest_value = value

    return lowest


def choose_central_atom(atoms: dict):

    candidates = get_candidates(atoms)

    candidates = remove_terminal_atoms(candidates)

    result = choose_if_only_one(candidates)

    if result is not None:

        return result

    return compare_electronegativity(candidates)


if __name__ == "__main__":

    examples = [

        {"C": 1, "O": 2},
        {"N": 1, "H": 3},
        {"O": 1, "H": 2},
        {"S": 1, "O": 4},
        {"P": 1, "Cl": 5},
        {"Xe": 1, "F": 4},
        {"Br": 1, "F": 3}

    ]

    print("===== CENTRAL ATOM ENGINE =====\n")

    for atoms in examples:

        print("Atoms:", atoms)

        print(
            "Central atom:",
            choose_central_atom(atoms)
        )

        print("-" * 35)