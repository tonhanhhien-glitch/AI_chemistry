def find_resonance_candidates(
    atom_objects: dict,
    bonds: list
):
    """
    Find bonds that may participate
    in resonance.

    A resonance candidate is a bond
    connected to an atom that has
    lone-pair electrons and can form
    a multiple bond.
    """

    candidates = []

    for bond in bonds:

        atom1_id = bond["atom1"]
        atom2_id = bond["atom2"]

        atom1 = atom_objects[atom1_id]
        atom2 = atom_objects[atom2_id]

        if (
            atom1["lone_electrons"] >= 2
            and bond["bond_order"] < 2
        ):

            candidates.append({
                "donor_atom": atom1_id,
                "other_atom": atom2_id,
                "bond": bond
            })

        if (
            atom2["lone_electrons"] >= 2
            and bond["bond_order"] < 2
        ):

            candidates.append({
                "donor_atom": atom2_id,
                "other_atom": atom1_id,
                "bond": bond
            })

    return candidates

def generate_resonance_structure(
    atom_objects: dict,
    bonds: list,
    candidate: dict
):
    """
    Generate one resonance structure by moving
    one lone pair from the donor atom into the bond.
    """

    donor_id = candidate["donor_atom"]
    target_bond = candidate["bond"]

    # Donor must have a lone pair
    if atom_objects[donor_id]["lone_electrons"] < 2:
        return None

    # Copy atom data
    new_atoms = {}

    for atom_id, atom in atom_objects.items():
        new_atoms[atom_id] = atom.copy()

    # Copy bonds
    new_bonds = []

    for bond in bonds:
        new_bonds.append(bond.copy())

    # Find corresponding bond
    for bond in new_bonds:

        if (
            bond["atom1"] == target_bond["atom1"]
            and
            bond["atom2"] == target_bond["atom2"]
        ):

            bond["bond_order"] += 1
            break

    # Remove one lone pair from donor
    new_atoms[donor_id]["lone_electrons"] -= 2

    return {
        "atom_objects": new_atoms,
        "bonds": new_bonds
    }

def validate_resonance_structure(
    atom_objects: dict,
    expected_charge: int = 0
):
    """
    Validate a resonance structure using:

    1. Formal charge
    2. Total molecular charge
    3. Octet / duet rules
    """

    from chemistry.formal_charge import (
        calculate_formal_charges,
        calculate_total_formal_charge,
        validate_total_formal_charge
    )

    from chemistry.lewis_engine import (
        check_octet,
        find_octet_deficient_atoms
    )

    formal_charges = calculate_formal_charges(
        atom_objects
    )

    total_charge = calculate_total_formal_charge(
        formal_charges
    )

    valid_charge = validate_total_formal_charge(
        formal_charges,
        expected_charge
    )

    check_octet(
        atom_objects
    )

    deficient_atoms = find_octet_deficient_atoms(
        atom_objects
    )

    valid_octet = (
        len(deficient_atoms) == 0
    )

    return {
        "formal_charges": formal_charges,
        "total_charge": total_charge,
        "expected_charge": expected_charge,
        "charge_valid": valid_charge,
        "octet_valid": valid_octet,
        "octet_deficient_atoms": deficient_atoms,
        "valid": (
            valid_charge
            and valid_octet
        )
    }

def resolve_resonance(
    atom_objects: dict,
    bonds: list,
    expected_charge: int = 0
):
    """
    Repeatedly form multiple bonds until
    the Lewis structure satisfies charge
    and octet requirements.
    """

    current_atoms = atom_objects
    current_bonds = bonds

    while True:

        # Check current structure
        validation = validate_resonance_structure(
            current_atoms,
            expected_charge
        )

        # Structure is already valid
        if validation["valid"]:
            return {
                "atom_objects": current_atoms,
                "bonds": current_bonds,
                "validation": validation
            }

        deficient_atoms = (
            validation[
                "octet_deficient_atoms"
            ]
        )

        if not deficient_atoms:
            return {
                "atom_objects": current_atoms,
                "bonds": current_bonds,
                "validation": validation
            }

        # Find possible donor
        candidates = find_resonance_candidates(
            current_atoms,
            current_bonds
        )

        selected_candidate = None

        for candidate in candidates:

            if (
                candidate["other_atom"]
                in deficient_atoms
            ):
                selected_candidate = candidate
                break

        if selected_candidate is None:
            return {
                "atom_objects": current_atoms,
                "bonds": current_bonds,
                "validation": validation
            }

        # Generate next structure
        generated = generate_resonance_structure(
            current_atoms,
            current_bonds,
            selected_candidate
        )

        if generated is None:
            return {
                "atom_objects": current_atoms,
                "bonds": current_bonds,
                "validation": validation
            }

        current_atoms = generated[
            "atom_objects"
        ]

        current_bonds = generated[
            "bonds"
        ]

        # Update bond information
        from chemistry.lewis_engine import (
            update_atom_bond_information
        )

        update_atom_bond_information(
            current_atoms,
            current_bonds
        )

if __name__ == "__main__":

    print("===== RESONANCE ENGINE TEST =====")

    atom_objects = {
        "C1": {
            "symbol": "C",
            "lone_electrons": 0
        },

        "O1": {
            "symbol": "O",
            "lone_electrons": 6
        },

        "O2": {
            "symbol": "O",
            "lone_electrons": 6
        }
    }

    bonds = [
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

    candidates = find_resonance_candidates(
        atom_objects,
        bonds
    )

    print()
    print("Resonance Candidates:")
    print(candidates)