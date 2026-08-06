from chemistry.valence_rules import calculate_total_valence

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

        atom_objects = create_atom_objects(atoms)

        bonds = create_skeleton(
            atom_objects,
            center
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

        print()

        print("Electron Summary:")
        print(electron_info)

        print("-" * 40)