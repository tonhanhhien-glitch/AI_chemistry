from chemistry.valence_rules import get_valence


def calculate_formal_charge(
    atom: dict,
    valence_electrons: int
):
    """
    Calculate the formal charge of an atom.

    Formula:

    Formal charge =
    valence electrons
    - nonbonding electrons
    - bonding electrons / 2
    """

    nonbonding_electrons = (
        atom["lone_electrons"]
    )

    bonding_electrons = (
        atom["bonding_electrons"]
    )

    formal_charge = (
        valence_electrons
        - nonbonding_electrons
        - bonding_electrons // 2
    )

    return formal_charge


def calculate_formal_charges(
    atom_objects: dict
):
    """
    Calculate formal charge for every atom.
    """

    formal_charges = {}

    for atom_id, atom in atom_objects.items():

        symbol = atom["symbol"]

        valence_electrons = get_valence(
            symbol
        )

        formal_charges[atom_id] = (
            calculate_formal_charge(
                atom,
                valence_electrons
            )
        )

    return formal_charges

def calculate_total_formal_charge(
    formal_charges: dict
):
    """
    Calculate the total formal charge
    of a molecule or ion.
    """

    total_charge = 0

    for charge in formal_charges.values():

        total_charge += charge

    return total_charge

def validate_total_formal_charge(
    formal_charges: dict,
    expected_charge: int
):
    """
    Validate whether the total formal charge
    matches the expected molecular or ionic charge.
    """

    total_charge = calculate_total_formal_charge(
        formal_charges
    )

    return total_charge == expected_charge

if __name__ == "__main__":

    print(
        "===== FORMAL CHARGE ENGINE TEST ====="
    )

    examples = [

        (
            "CO2",
            {
                "C1": {
                    "symbol": "C",
                    "bonding_electrons": 8,
                    "lone_electrons": 0
                },
                "O1": {
                    "symbol": "O",
                    "bonding_electrons": 4,
                    "lone_electrons": 4
                },
                "O2": {
                    "symbol": "O",
                    "bonding_electrons": 4,
                    "lone_electrons": 4
                }
            }
        ),

        (
            "H2O",
            {
                "O1": {
                    "symbol": "O",
                    "bonding_electrons": 4,
                    "lone_electrons": 4
                },
                "H1": {
                    "symbol": "H",
                    "bonding_electrons": 2,
                    "lone_electrons": 0
                },
                "H2": {
                    "symbol": "H",
                    "bonding_electrons": 2,
                    "lone_electrons": 0
                }
            }
        ),

        (
            "N2",
            {
                "N1": {
                    "symbol": "N",
                    "bonding_electrons": 6,
                    "lone_electrons": 2
                },
                "N2": {
                    "symbol": "N",
                    "bonding_electrons": 6,
                    "lone_electrons": 2
                }
            }
        )
    ]

    for name, atom_objects in examples:

        result = calculate_formal_charges(
            atom_objects
        )

        print()
        print(name)

        print("Formal Charges:")
        print(result)

        total_charge = calculate_total_formal_charge(
            result
        )

        print(
            "Total Formal Charge:",
            total_charge
        )

        print("-" * 40)

    print()
    print("===== ION CHARGE VALIDATION TEST =====")

    nh4_atom_objects = {

        "N1": {
            "symbol": "N",
            "bonding_electrons": 8,
            "lone_electrons": 0
        },

        "H1": {
            "symbol": "H",
            "bonding_electrons": 2,
            "lone_electrons": 0
        },

        "H2": {
            "symbol": "H",
            "bonding_electrons": 2,
            "lone_electrons": 0
        },

        "H3": {
            "symbol": "H",
            "bonding_electrons": 2,
            "lone_electrons": 0
        },

        "H4": {
            "symbol": "H",
            "bonding_electrons": 2,
            "lone_electrons": 0
        }
    }

    nh4_charges = calculate_formal_charges(
        nh4_atom_objects
    )

    print()
    print("NH4+ Formal Charges:")
    print(nh4_charges)

    nh4_total = calculate_total_formal_charge(
        nh4_charges
    )

    print(
        "Total Formal Charge:",
        nh4_total
    )

    print(
        "Expected Charge:",
        1
    )

    print(
        "Validation:",
        validate_total_formal_charge(
            nh4_charges,
            1
        )
    )
    print()
    print("===== OH- CHARGE VALIDATION TEST =====")

    oh_atom_objects = {

        "O1": {
            "symbol": "O",
            "bonding_electrons": 2,
            "lone_electrons": 6
        },

        "H1": {
            "symbol": "H",
            "bonding_electrons": 2,
            "lone_electrons": 0
        }
    }

    oh_charges = calculate_formal_charges(
        oh_atom_objects
    )

    print()
    print("OH- Formal Charges:")
    print(oh_charges)

    oh_total = calculate_total_formal_charge(
        oh_charges
    )

    print(
        "Total Formal Charge:",
        oh_total
    )

    print(
        "Expected Charge:",
        -1
    )

    print(
        "Validation:",
        validate_total_formal_charge(
            oh_charges,
            -1
        )
    )