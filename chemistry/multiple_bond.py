from chemistry.periodic_table import get_element

def find_multiple_bond_candidate(
    atom_objects: dict,
    bonds: list,
    deficient_atoms: list
):
    """
    Find a bond that can potentially be converted
    into a multiple bond.

    A candidate requires:
    - one atom is octet-deficient
    - the other atom is a bonded terminal atom
    - the terminal atom has at least one lone pair
    """

    for deficient_id in deficient_atoms:

        for bond in bonds:

            if bond["atom1"] == deficient_id:
                other_id = bond["atom2"]

            elif bond["atom2"] == deficient_id:
                other_id = bond["atom1"]

            else:
                continue

            other_atom = atom_objects[other_id]

            # Hydrogen cannot form multiple bonds
            if other_atom["symbol"] == "H":
                continue

            # Terminal atom must have a lone pair
            if other_atom["lone_electrons"] < 2:
                continue

            # Multiple bond engine only creates double bonds  
            if bond["bond_order"] >= 2:
                continue

            return {
                "deficient_atom": deficient_id,
                "donor_atom": other_id,
                "bond": bond
            }

    return None

def form_multiple_bond(
    atom_objects: dict,
    bonds: list,
    candidate: dict
):
    """
    Form one additional bond using one lone pair
    from the donor atom.
    """

    donor_id = candidate["donor_atom"]
    target_bond = candidate["bond"]

    # Donor must have at least one lone pair
    if atom_objects[donor_id]["lone_electrons"] < 2:
        return False

    # Increase bond order by one
    target_bond["bond_order"] += 1

    # Use one lone pair to form the new bond
    atom_objects[donor_id]["lone_electrons"] -= 2

    # Recalculate bonding information
    for atom in atom_objects.values():

        atom["bond_count"] = 0
        atom["bonding_electrons"] = 0

    for bond in bonds:

        atom1_id = bond["atom1"]
        atom2_id = bond["atom2"]

        bond_order = bond["bond_order"]

        bonding_electrons = (
            bond_order * 2
        )

        atom_objects[
            atom1_id
        ]["bond_count"] += 1

        atom_objects[
            atom2_id
        ]["bond_count"] += 1

        atom_objects[
            atom1_id
        ]["bonding_electrons"] += (
            bonding_electrons
        )

        atom_objects[
            atom2_id
        ]["bonding_electrons"] += (
            bonding_electrons
        )

    return True

def form_all_multiple_bonds(
    atom_objects: dict,
    bonds: list,
    deficient_atoms: list,
    check_octet_function
):
    """
    Repeatedly form multiple bonds until all
    deficient atoms satisfy their electron rule
    or no valid candidate remains.
    """

    while deficient_atoms:

        candidate = find_multiple_bond_candidate(
            atom_objects,
            bonds,
            deficient_atoms
        )

        if candidate is None:
            break

        result = form_multiple_bond(
            atom_objects,
            bonds,
            candidate
        )

        if not result:
            break

        check_octet_function(
            atom_objects
        )

        deficient_atoms = [
            atom_id
            for atom_id, atom in atom_objects.items()
            if not atom["octet"]
        ]

    return {
        "atom_objects": atom_objects,
        "bonds": bonds,
        "deficient_atoms": deficient_atoms
    }

if __name__ == "__main__":

    print("===== TRIPLE BOND ENGINE TEST =====")

    atom_objects = {
        "N1": {
            "symbol": "N",
            "bond_count": 1,
            "bonding_electrons": 2,
            "lone_electrons": 6,
            "octet": True
        },

        "N2": {
            "symbol": "N",
            "bond_count": 1,
            "bonding_electrons": 2,
            "lone_electrons": 2,
            "octet": False
        }
    }

    bonds = [
        {
            "atom1": "N1",
            "atom2": "N2",
            "bond_order": 1
        }
    ]

    deficient_atoms = [
        "N2"
    ]

    def test_check_octet(atom_objects):

        for atom in atom_objects.values():

            electron_count = (
                atom["bonding_electrons"]
                + atom["lone_electrons"]
            )

            if atom["symbol"] == "H":

                atom["octet"] = (
                    electron_count == 2
                )

            else:

                atom["octet"] = (
                    electron_count == 8
                )

        return atom_objects

    print()
    print("Before:")
    print(atom_objects)
    print(bonds)

    result = form_all_multiple_bonds(
        atom_objects,
        bonds,
        deficient_atoms,
        test_check_octet
    )

    print()
    print("After:")
    print(result["atom_objects"])

    print()
    print("Final Bonds:")
    print(result["bonds"])

    print()
    print(
        "Remaining deficient atoms:",
        result["deficient_atoms"]
    )