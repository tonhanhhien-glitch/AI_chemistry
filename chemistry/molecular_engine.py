from chemistry.lewis_engine import build_lewis_structure
from chemistry.vsepr_rules import analyze_vsepr
from chemistry.geometry_3d import (
    generate_adjusted_ligand_positions,
    scale_vector,
    validate_molecular_angles
)


# ============================================================
# BOND LENGTH DATA
# ============================================================

BOND_LENGTHS = {
    "H2O": [0.96, 0.96],
    "NH3": [1.01, 1.01, 1.01],
    "CH4": [1.09, 1.09, 1.09, 1.09],
    "CO2": [1.16, 1.16],
}


def build_formula(atoms):
    """
    Convert atom dictionary into a normalized formula string.

    Formula ordering:
        C first
        H second
        Other elements alphabetically

    Examples:
        {"O": 1, "H": 2} -> "H2O"
        {"C": 1, "O": 2} -> "CO2"
        {"N": 1, "H": 3} -> "NH3"
    """

    symbols = list(atoms.keys())

    if "C" in symbols:

        ordered_symbols = ["C"]

        if "H" in symbols:
            ordered_symbols.append("H")

        ordered_symbols.extend(
            sorted(
                symbol
                for symbol in symbols
                if symbol not in {"C", "H"}
            )
        )

    else:

        ordered_symbols = sorted(symbols)


    formula = ""

    for symbol in ordered_symbols:

        count = atoms[symbol]

        formula += symbol

        if count != 1:
            formula += str(count)

    return formula


def get_ligand_atoms(
    atom_objects,
    central_id
):
    """
    Get atoms directly bonded to the central atom.

    Returns:
        list of atom IDs
    """

    ligand_atoms = []

    for atom_id, atom_data in atom_objects.items():

        if atom_id == central_id:
            continue

        if atom_data["bond_count"] > 0:
            ligand_atoms.append(atom_id)

    return ligand_atoms


def analyze_molecule(
    atoms,
    central_atom,
    charge=0
):
    """
    Complete chemistry analysis pipeline:

        Formula
            ↓
        Lewis structure
            ↓
        VSEPR
            ↓
        3D coordinates
            ↓
        Molecular angle validation
    """

    # ========================================================
    # STEP 1 — LEWIS STRUCTURE
    # ========================================================

    lewis_result = build_lewis_structure(
        atoms,
        central_atom,
        charge
    )


    # ========================================================
    # STEP 2 — FIND CENTRAL ATOM ID
    # ========================================================

    central_id = None

    for atom_id, atom_data in lewis_result["atom_objects"].items():

        if atom_data["symbol"] == central_atom:

            central_id = atom_id
            break


    if central_id is None:

        raise ValueError(
            f"Central atom {central_atom} was not found."
        )


    # ========================================================
    # STEP 3 — VSEPR
    # ========================================================

    vsepr_result = analyze_vsepr(
        lewis_result["atom_objects"],
        lewis_result["bonds"],
        central_id
    )


    # ========================================================
    # STEP 4 — BUILD FORMULA
    # ========================================================

    formula = build_formula(atoms)


    # ========================================================
    # STEP 5 — GET BOND LENGTHS
    # ========================================================

    if formula not in BOND_LENGTHS:

        raise ValueError(
            f"No bond-length data available for {formula}."
        )

    bond_lengths = BOND_LENGTHS[formula]


    # ========================================================
    # STEP 6 — GET LIGAND ATOMS
    # ========================================================

    ligand_atoms = get_ligand_atoms(
        lewis_result["atom_objects"],
        central_id
    )


    # ========================================================
    # STEP 7 — VALIDATE LIGAND COUNT
    # ========================================================

    if len(ligand_atoms) != vsepr_result["bonding_domains"]:

        raise ValueError(
            "Number of ligand atoms does not match "
            "the number of bonding domains."
        )


    if len(bond_lengths) != len(ligand_atoms):

        raise ValueError(
            "Number of bond lengths does not match "
            "the number of ligand atoms."
        )


    # ========================================================
    # STEP 8 — GENERATE 3D COORDINATES
    # ========================================================

    # ==================================================
    # 3D MOLECULAR COORDINATES
    # ==================================================

    bonding_domains = (
        vsepr_result["bonding_domains"]
    )

    characteristic_angle = (
        vsepr_result["characteristic_bond_angle"]
    )

    molecular_geometry = (
        vsepr_result["molecular_geometry"]
    )

    ligand_positions = (
        generate_adjusted_ligand_positions(
            molecular_geometry,
            bonding_domains,
            characteristic_angle
        )
    )

    coordinates = [
        {
            "atom_index": 0,
            "role": "central",
            "coordinate": [
                0.0,
                0.0,
                0.0
            ]
        }
    ]

    for index, (
        ligand_position,
        bond_length
    ) in enumerate(
        zip(
            ligand_positions,
            bond_lengths
        ),
        start=1
    ):

        displacement = scale_vector(
            ligand_position,
            bond_length
        )

        coordinate = [
            displacement[0],
            displacement[1],
            displacement[2]
        ]

        coordinates.append({
            "atom_index": index,
            "role": "ligand",
            "coordinate": coordinate
        })

    # ========================================================
    # STEP 9 — VALIDATE MOLECULAR ANGLES
    # ========================================================

    angle_validation = validate_molecular_angles(
        coordinates[1:],
        vsepr_result["characteristic_bond_angle"]
    )


    # ========================================================
    # STEP 10 — FINAL RESULT
    # ========================================================

    return {

        "formula": formula,

        "central_atom": central_id,

        "lewis": lewis_result,

        "vsepr": vsepr_result,

        "ligand_atoms": ligand_atoms,

        "bond_lengths": bond_lengths,

        "coordinates": coordinates,

        "angle_validation": angle_validation
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 40)
    print("===== MOLECULAR ENGINE TEST =====")
    print("=" * 40)


    result = analyze_molecule(
        {
            "O": 1,
            "H": 2
        },
        "O"
    )


    print()
    print("===== FORMULA =====")

    print(
        result["formula"]
    )


    print()
    print("===== LEWIS =====")

    print(
        result["lewis"]
    )


    print()
    print("===== VSEPR =====")

    print(
        result["vsepr"]
    )


    print()
    print("===== LIGAND ATOMS =====")

    print(
        result["ligand_atoms"]
    )


    print()
    print("===== BOND LENGTHS =====")

    print(
        result["bond_lengths"]
    )


    print()
    print("===== 3D COORDINATES =====")

    for coordinate in result["coordinates"]:

        print(
            coordinate
        )


    print()
    print("===== ANGLE VALIDATION =====")

    print(
        result["angle_validation"]
    )