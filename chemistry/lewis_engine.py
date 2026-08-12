from chemistry.valence_rules import (
    calculate_total_valence,
)
from chemistry.multiple_bond import (
    form_all_multiple_bonds
)
from chemistry.formal_charge import (
    calculate_formal_charges,
    calculate_total_formal_charge
)
from chemistry.resonance_detector import (
    resolve_resonance
)
from chemistry.periodic_table import get_element

def create_atom_objects(atoms: dict):

    atom_objects = {}

    for symbol, count in atoms.items():

        for i in range(1, count + 1):

            atom_id = f"{symbol}{i}"

            atom_objects[atom_id] = {

                "symbol": symbol,

                "bond_count": 0,

                "bonding_electrons": 0,

                "lone_electrons": 0,

                "octet": 0

            }

    return atom_objects

def create_skeleton(
    atom_objects: dict,
    central_atom: str
):

    bonds = []

    # tìm ID của nguyên tử trung tâm
    central_id = None

    for atom_id, atom in atom_objects.items():

        if atom["symbol"] == central_atom:

            central_id = atom_id

            break

    # tạo liên kết
    for atom_id, atom in atom_objects.items():

        if atom_id == central_id:
            continue

        bonds.append({

            "atom1": central_id,

            "atom2": atom_id,

            "bond_order": 1

        })

    return bonds

def update_atom_bond_information(
    atom_objects: dict,
    bonds: list
):
    """
    Update bond count and bonding electrons
    for each atom based on the current Lewis skeleton.
    """

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

    return atom_objects

def count_bonding_electrons(bonds: list):

    total = 0

    for bond in bonds:
        total += bond["bond_order"] * 2

    return total

def calculate_remaining_electrons(
    atoms: dict,
    bonds: list,
):

    total_valence = calculate_total_valence(atoms)

    bonding = count_bonding_electrons(bonds)

    remaining = total_valence - bonding

    return {
        "total_valence": total_valence,
        "bonding_electrons": bonding,
        "remaining_electrons": remaining,
    }

def calculate_remaining_electrons_with_charge(
    atoms: dict,
    bonds: list,
    charge: int
):
    """
    Calculate remaining electrons while
    accounting for molecular or ionic charge.
    """

    total_valence = calculate_total_valence(
        atoms
    )

    # Positive charge removes electrons
    # Negative charge adds electrons
    total_valence -= charge

    bonding = count_bonding_electrons(
        bonds
    )

    remaining = (
        total_valence - bonding
    )

    return {
        "total_valence": total_valence,
        "bonding_electrons": bonding,
        "remaining_electrons": remaining
    }

def distribute_lone_electrons(
    atom_objects: dict,
    bonds: list,
    remaining_electrons: int
):
    """
    Distribute remaining electrons as lone pairs.

    Step 1:
    Give electrons to terminal atoms that need
    electrons to complete their octet.

    Step 2:
    Give any remaining electrons to the central
    atom.

    Hydrogen follows the duet rule and does not
    receive lone-pair electrons.
    """

    # -----------------------------------------
    # STEP 1: Terminal atoms
    # -----------------------------------------

    for atom_id, atom in atom_objects.items():

        if atom["symbol"] == "H":
            continue

        bonded_atoms = []

        for bond in bonds:

            if bond["atom1"] == atom_id:

                bonded_atoms.append(
                    bond["atom2"]
                )

            elif bond["atom2"] == atom_id:

                bonded_atoms.append(
                    bond["atom1"]
                )

        # Terminal atom = exactly one bond
        if len(bonded_atoms) == 1:

            electrons_needed = (
                8
                - atom["bonding_electrons"]
                - atom["lone_electrons"]
            )

            if electrons_needed > 0:

                electrons_to_add = min(
                    electrons_needed,
                    remaining_electrons
                )

                atom["lone_electrons"] += (
                    electrons_to_add
                )

                remaining_electrons -= (
                    electrons_to_add
                )

        if remaining_electrons <= 0:
            return remaining_electrons

    # -----------------------------------------
    # STEP 2: Central atom
    # -----------------------------------------

    central_atom = None
    central_id = None

    for atom_id, atom in atom_objects.items():

        bonded_atoms = []

        for bond in bonds:

            if bond["atom1"] == atom_id:

                bonded_atoms.append(
                    bond["atom2"]
                )

            elif bond["atom2"] == atom_id:

                bonded_atoms.append(
                    bond["atom1"]
                )

        # Non-terminal atom = central atom
        if len(bonded_atoms) > 1:

            central_id = atom_id
            central_atom = atom

            break

    if central_atom is not None:

        electrons_needed = (
            8
            - central_atom["bonding_electrons"]
            - central_atom["lone_electrons"]
        )

        if electrons_needed > 0:

            electrons_to_add = min(
                electrons_needed,
                remaining_electrons
            )

            central_atom["lone_electrons"] += (
                electrons_to_add
            )

            remaining_electrons -= (
                electrons_to_add
            )

    return remaining_electrons

def check_octet(atom_objects: dict):
    """
    Check whether each atom satisfies its electron rule.

    Hydrogen follows the duet rule.

    Other atoms use the maximum allowed electron
    count defined in the periodic table.
    """

    for atom in atom_objects.values():

        symbol = atom["symbol"]

        element = get_element(symbol)

        if element is None:

            atom["octet"] = False

            continue

        electron_count = (
            atom["bonding_electrons"]
            + atom["lone_electrons"]
        )

        if symbol == "H":

            target_electrons = 2

        else:

            target_electrons = element[
                "max_octet"
            ]

        atom["octet"] = (
            electron_count == target_electrons
        )

    return atom_objects

def find_octet_deficient_atoms(
    atom_objects: dict
 ):
    """
    Find atoms that do not satisfy their
    electron rule.
    """

    deficient_atoms = []

    for atom_id, atom in atom_objects.items():

        if not atom["octet"]:

            deficient_atoms.append(
                atom_id
            )

    return deficient_atoms

def build_lewis_structure(
    atoms: dict,
    central_atom: str,
    expected_charge: int = 0
):
    """
    Build a complete Lewis structure.

    Pipeline:
    1. Create atom objects
    2. Create skeleton
    3. Update bond information
    4. Calculate valence electrons
    5. Distribute lone electrons
    6. Check octet / duet
    7. Resolve multiple bonds
    8. Calculate formal charges
    9. Validate final charge
    """

    # -----------------------------------------
    # STEP 1: Atom objects
    # -----------------------------------------

    atom_objects = create_atom_objects(
        atoms
    )

    # -----------------------------------------
    # STEP 2: Skeleton
    # -----------------------------------------

    bonds = create_skeleton(
        atom_objects,
        central_atom
    )

    # -----------------------------------------
    # STEP 3: Bond information
    # -----------------------------------------

    update_atom_bond_information(
        atom_objects,
        bonds
    )

    # -----------------------------------------
    # STEP 4: Electron calculation
    # -----------------------------------------

    electron_info = (
        calculate_remaining_electrons_with_charge(
            atoms,
            bonds,
            expected_charge
        )
    )

    remaining_electrons = (
        electron_info["remaining_electrons"]
    )

    # -----------------------------------------
    # STEP 5: Lone electrons
    # -----------------------------------------

    remaining_electrons = (
        distribute_lone_electrons(
            atom_objects,
            bonds,
            remaining_electrons
        )
    )

    # -----------------------------------------
    # STEP 6: Octet check
    # -----------------------------------------

    check_octet(
        atom_objects
    )

    # -----------------------------------------
    # STEP 7: Multiple bond resolution
    # -----------------------------------------

    deficient_atoms = (
        find_octet_deficient_atoms(
            atom_objects
        )
    )

    while deficient_atoms:

        from chemistry.multiple_bond import (
            find_multiple_bond_candidate,
            form_multiple_bond
        )

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

        update_atom_bond_information(
            atom_objects,
            bonds
        )

        check_octet(
            atom_objects
        )

        deficient_atoms = (
            find_octet_deficient_atoms(
                atom_objects
            )
        )

    # -----------------------------------------
    # STEP 7B: Resonance resolution
    # -----------------------------------------

    if deficient_atoms:

        resonance_result = resolve_resonance(
            atom_objects,
            bonds,
            expected_charge
        )

        atom_objects = resonance_result[
            "atom_objects"
        ]

        bonds = resonance_result[
            "bonds"
        ]

        update_atom_bond_information(
            atom_objects,
            bonds
        )

        check_octet(
            atom_objects
        )

        deficient_atoms = (
            find_octet_deficient_atoms(
                atom_objects
            )
        )

    # -----------------------------------------
    # STEP 8: Formal charge
    # -----------------------------------------

    formal_charges = calculate_formal_charges(
        atom_objects
    )

    total_formal_charge = (
        calculate_total_formal_charge(
            formal_charges
        )
    )

    # -----------------------------------------
    # STEP 9: Charge validation
    # -----------------------------------------

    charge_valid = (
        total_formal_charge
        == expected_charge
    )

    return {
        "atom_objects": atom_objects,
        "bonds": bonds,
        "electron_info": electron_info,
        "remaining_electrons": remaining_electrons,
        "formal_charges": formal_charges,
        "total_formal_charge": (
            total_formal_charge
        ),
        "expected_charge": expected_charge,
        "charge_valid": charge_valid,
        "octet_deficient_atoms": (
            deficient_atoms
        )
    }

if __name__ == "__main__":

    examples = [

        (
            {"C": 1, "O": 2},
            "C",
        ),

        (
            {"O": 1, "H": 2},
            "O",
        ),

        (
            {"N": 1, "H": 3},
            "N",
        ),

    ]

    print("===== LEWIS ENGINE : STEP 1 =====\n")

    for atoms, center in examples:

        atom_objects = create_atom_objects(atoms)

        print("Atom Objects:")
        print(atom_objects)
        print()

        print("Atoms:", atoms)
        print("Central:", center)

        bonds = create_skeleton(
            atom_objects,
            center
        )

        update_atom_bond_information(
            atom_objects,
            bonds
        )

        print(
            "Updated Atom Objects:"
        )

        print(
            atom_objects
        )

        print("Skeleton:")
        print(bonds)
        print()

        print(
            "Bonding electrons:",
            count_bonding_electrons(bonds),
        )

        electron_info = calculate_remaining_electrons(
            atoms,
            bonds,
        )

        remaining_electrons = electron_info[
            "remaining_electrons"
        ]

        print()
        print("Electron Summary:")
        print(electron_info)

        remaining_electrons = distribute_lone_electrons(
            atom_objects,
            bonds,
            remaining_electrons
        )

        print()
        print("After Lone Electron Distribution:")
        print(atom_objects)

        print(
            "Remaining electrons:",
            remaining_electrons
        )

        check_octet(
            atom_objects
        )

        print()
        print("After Octet Check:")
        print(atom_objects)

        deficient_atoms = find_octet_deficient_atoms(
            atom_objects
        )

        multiple_bond_result = form_all_multiple_bonds(
            atom_objects,
            bonds,
            deficient_atoms,
            check_octet
        )

        atom_objects = multiple_bond_result[
            "atom_objects"
        ]

        bonds = multiple_bond_result[
            "bonds"
        ]

        deficient_atoms = multiple_bond_result[
            "deficient_atoms"
        ]

        print()
        print("After Multiple Bond Formation:")
        print(atom_objects)

        print()
        print("Final Bonds:")
        print(bonds)

        print()
        print(
            "Final Octet Deficient Atoms:",
            deficient_atoms
        )

        print()
        print(
            "Octet deficient atoms:",
            deficient_atoms
        )

        print("-" * 40)

    print()
    print("===== REMAINING ELECTRONS TEST =====")

    test_atoms = {
        "C": 1,
        "O": 2
    }

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

    remaining_electrons = calculate_remaining_electrons(
        test_atoms,
        test_bonds
    )

    print(
        "Atoms:",
        test_atoms
    )

    print(
        "Bonding electrons:",
        count_bonding_electrons(test_bonds)
    )

    print(
        "Remaining electrons:",
        remaining_electrons
    )