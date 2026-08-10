"""
Bond Polarity Engine

Uses electronegativity differences to classify chemical bonds.

Classification:
    delta_chi < 0.4
        Nonpolar covalent

    0.4 <= delta_chi < 1.7
        Polar covalent

    delta_chi >= 1.7
        Ionic
"""

from chemistry.periodic_table import get_electronegativity


NONPOLAR_LIMIT = 0.4
IONIC_LIMIT = 1.7

def get_atom_symbol(atom_id: str):

    for index, character in enumerate(atom_id):

        if character.isdigit():

            return atom_id[:index]

    return atom_id

def calculate_electronegativity_difference(
    atom1: str,
    atom2: str
):
    """
    Calculate the absolute electronegativity difference
    between two atoms.
    """

    electronegativity_1 = get_electronegativity(atom1)
    electronegativity_2 = get_electronegativity(atom2)

    if electronegativity_1 is None:
        raise ValueError(
            f"Electronegativity is not available for {atom1}"
        )

    if electronegativity_2 is None:
        raise ValueError(
            f"Electronegativity is not available for {atom2}"
        )

    return abs(
        electronegativity_1 - electronegativity_2
    )

def analyze_bond(bond: dict):

    atom1_id = bond["atom1"]
    atom2_id = bond["atom2"]

    atom1 = get_atom_symbol(atom1_id)
    atom2 = get_atom_symbol(atom2_id)

    polarity_info = classify_bond_polarity(
        atom1,
        atom2
    )

    return {
        "atom1": atom1_id,
        "atom2": atom2_id,
        "bond_order": bond["bond_order"],
        "electronegativity_1": polarity_info[
            "electronegativity_1"
        ],
        "electronegativity_2": polarity_info[
            "electronegativity_2"
        ],
        "delta_chi": polarity_info[
            "delta_chi"
        ],
        "polarity": polarity_info[
            "classification"
        ],
        "more_electronegative_atom": (
            polarity_info[
                "more_electronegative_atom"
            ]
        ),
        "less_electronegative_atom": (
            polarity_info[
                "less_electronegative_atom"
            ]
        )
    }


def analyze_bonds(bonds: list):

    analyzed_bonds = []

    for bond in bonds:

        analyzed_bond = analyze_bond(
            bond
        )

        analyzed_bonds.append(
            analyzed_bond
        )

    return analyzed_bonds

def classify_bond_polarity(
    atom1: str,
    atom2: str
):
    """
    Classify a chemical bond based on
    electronegativity difference.
    """

    electronegativity_1 = get_electronegativity(atom1)
    electronegativity_2 = get_electronegativity(atom2)

    difference = calculate_electronegativity_difference(
        atom1,
        atom2
    )

    if difference < NONPOLAR_LIMIT:

        classification = "nonpolar covalent"

    elif difference < IONIC_LIMIT:

        classification = "polar covalent"

    else:

        classification = "ionic"

    if electronegativity_1 > electronegativity_2:

        more_electronegative_atom = atom1
        less_electronegative_atom = atom2

    elif electronegativity_2 > electronegativity_1:

        more_electronegative_atom = atom2
        less_electronegative_atom = atom1

    else:

        more_electronegative_atom = None
        less_electronegative_atom = None

    return {
        "atom1": atom1,
        "atom2": atom2,
        "electronegativity_1": electronegativity_1,
        "electronegativity_2": electronegativity_2,
        "delta_chi": round(difference, 2),
        "classification": classification,
        "more_electronegative_atom": more_electronegative_atom,
        "less_electronegative_atom": less_electronegative_atom
    }


if __name__ == "__main__":

    examples = [
        ("C", "H"),
        ("C", "O"),
        ("O", "H"),
        ("Na", "Cl"),
        ("H", "F"),
        ("S", "O")
    ]

    print("===== BOND POLARITY ENGINE =====")
    print()

    for atom1, atom2 in examples:

        result = classify_bond_polarity(
            atom1,
            atom2
        )

        print(
            f"{atom1}-{atom2}:",
            result
        )

        print("-" * 50)

        print("===== ATOM ID TEST =====")
        print(get_atom_symbol("C1"))
        print(get_atom_symbol("O2"))
        print(get_atom_symbol("N1"))

        print()
        print("===== BOND ANALYSIS TEST =====")

        test_bond = {
        "atom1": "C1",
        "atom2": "O1",
        "bond_order": 1
        }

        print(
            analyze_bond(test_bond)
        )

        print()
        print("===== ALL BONDS TEST =====")

        test_bonds = [
            {
                "atom1": "C1",
                "atom2": "O1",
                "bond_order": 1
            },
            {
                "atom1": "C1",
                "atom2": "O2",
                "bond_order": 1
            }
        ]

        analyzed_bonds = analyze_bonds(
            test_bonds
        )

        for bond in analyzed_bonds:
            print(bond)