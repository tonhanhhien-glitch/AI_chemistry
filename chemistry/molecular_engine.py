import math

from chemistry.lewis_engine import build_lewis_structure
from chemistry.vsepr_rules import analyze_vsepr
from chemistry.geometry_3d import (
    generate_molecular_coordinates,
    generate_adjusted_ligand_positions,
    get_ligand_positions,
    validate_molecular_angles,
    get_valid_molecular_angles,
    scale_vector,
)
from .resonance_detector import resolve_resonance
from chemistry.resonance_detector import resolve_resonance

# ============================================================
# BOND LENGTH DATA
# ============================================================

BOND_LENGTHS = {
    "H2O": [0.96, 0.96],
    "CO2": [1.16, 1.16],
    "NH3": [1.01, 1.01, 1.01],
    "CH4": [1.09, 1.09, 1.09, 1.09],
    "BF3": [1.30, 1.30, 1.30],
    "PCl5": [2.02, 2.02, 2.02, 2.02, 2.02],
    "SF6": [1.56, 1.56, 1.56, 1.56, 1.56, 1.56],

    "NH4": [1.01, 1.01, 1.01, 1.01],
    "H3O": [0.98, 0.98, 0.98],
    "OH": [0.97],

    "NO3": [1.24, 1.24, 1.24],
    "CO3": [1.28, 1.28, 1.28],
    "SO4": [1.47, 1.47, 1.47, 1.47],
    "PO4": [1.54, 1.54, 1.54, 1.54],
}


# ============================================================
# 3D LIGAND POSITION ADAPTER
# ============================================================

def _generate_two_ligand_positions(angle_degrees):
    """
    Generate two unit vectors with the requested angle between them.
    The vectors lie in the XY plane.
    """
    angle_radians = math.radians(angle_degrees)

    return [
        [1.0, 0.0, 0.0],
        [
            math.cos(angle_radians),
            math.sin(angle_radians),
            0.0
        ]
    ]


def _generate_three_pyramidal_positions(angle_degrees):
    """
    Generate three unit ligand vectors for a trigonal-pyramidal
    molecular geometry with the requested ligand-ligand angle.

    The three vectors are arranged symmetrically around the Z axis.
    """
    angle_radians = math.radians(angle_degrees)

    # For three equivalent vectors with azimuthal separation 120°:
    # cos(theta) = z^2 + (1-z^2) * cos(120°)
    #             = 1.5*z^2 - 0.5
    # where theta is the requested ligand-ligand angle.
    cosine_theta = math.cos(angle_radians)
    z_squared = (cosine_theta + 0.5) / 1.5

    if z_squared < 0 or z_squared > 1:
        raise ValueError(
            "Characteristic angle cannot generate a valid "
            "trigonal-pyramidal geometry."
        )

    z = math.sqrt(z_squared)
    radius = math.sqrt(1.0 - z_squared)

    return [
        [
            radius,
            0.0,
            z
        ],
        [
            -0.5 * radius,
            (math.sqrt(3.0) / 2.0) * radius,
            z
        ],
        [
            -0.5 * radius,
            -(math.sqrt(3.0) / 2.0) * radius,
            z
        ]
    ]

def build_formula(atoms):
    """
    Build normalized formula for supported molecules and ions.
    """

    normalized = frozenset(atoms.items())

    known_formulas = {

        frozenset({
            ("H", 2),
            ("O", 1)
        }): "H2O",

        frozenset({
            ("N", 1),
            ("H", 3)
        }): "NH3",

        frozenset({
            ("C", 1),
            ("H", 4)
        }): "CH4",

        frozenset({
            ("C", 1),
            ("O", 2)
        }): "CO2",

        frozenset({
            ("B", 1),
            ("F", 3)
        }): "BF3",

        frozenset({
            ("P", 1),
            ("Cl", 5)
        }): "PCl5",

        frozenset({
            ("S", 1),
            ("F", 6)
        }): "SF6",

                frozenset({
            ("N", 1),
            ("O", 3)
        }): "NO3",

        frozenset({
            ("C", 1),
            ("O", 3)
        }): "CO3",

        frozenset({
            ("S", 1),
            ("O", 4)
        }): "SO4",

        frozenset({
            ("P", 1),
            ("O", 4)
        }): "PO4",

        # ====================================================
        # CHARGED ION COMPOSITIONS
        # ====================================================

        frozenset({
            ("N", 1),
            ("H", 4)
        }): "NH4",

        frozenset({
            ("O", 1),
            ("H", 3)
        }): "H3O",

        frozenset({
            ("O", 1),
            ("H", 1)
        }): "OH",
    }

    if normalized in known_formulas:

        return known_formulas[normalized]

    raise ValueError(
        f"Formula normalization is not defined for "
        f"{dict(atoms)}."
    )
    """
    Build normalized formula from an atom-count dictionary.

    Examples:
        {"H": 2, "O": 1} -> "H2O"
        {"N": 1, "H": 3} -> "H3N"
        {"N": 1, "H": 4} -> "H4N"
        {"O": 1, "H": 3} -> "H3O"
        {"O": 1, "H": 1} -> "HO"

    Formula normalization is based only on
    the atom composition. Charge is handled
    separately by the molecular analysis engine.
    """

    if not isinstance(atoms, dict):
        raise ValueError(
            "Atoms must be provided as a dictionary."
        )

    if not atoms:
        raise ValueError(
            "Atoms dictionary cannot be empty."
        )

    # ========================================================
    # VALIDATE ATOM COUNTS
    # ========================================================

    for symbol, count in atoms.items():

        if not isinstance(symbol, str):
            raise ValueError(
                "Element symbols must be strings."
            )

        if not isinstance(count, int):
            raise ValueError(
                f"Atom count for {symbol} must be an integer."
            )

        if count <= 0:
            raise ValueError(
                f"Atom count for {symbol} must be greater than zero."
            )

    # ========================================================
    # FORMULA ORDER
    # ========================================================
    #
    # Use Hill-style ordering:
    #   1. Carbon first
    #   2. Hydrogen second
    #   3. Remaining elements alphabetically
    #
    # This keeps formulas deterministic.
    # ========================================================

    symbols = list(atoms.keys())

    ordered_symbols = []

    if "C" in atoms:
        ordered_symbols.append("C")

    if "H" in atoms:
        ordered_symbols.append("H")

    remaining_symbols = sorted(
        symbol
        for symbol in symbols
        if symbol not in {"C", "H"}
    )

    ordered_symbols.extend(
        remaining_symbols
    )

    # ========================================================
    # BUILD FORMULA
    # ========================================================

    formula_parts = []

    for symbol in ordered_symbols:

        count = atoms[symbol]

        if count == 1:
            formula_parts.append(symbol)

        else:
            formula_parts.append(
                f"{symbol}{count}"
            )

    return "".join(formula_parts)

def generate_adjusted_ligand_positions(
    molecular_geometry: str,
    bonding_domains: int,
    characteristic_bond_angle: float,
    lone_pair_domains: int = 0
):
    """
    Generate ligand direction vectors for the molecular geometry.

    Molecular geometry is handled separately from electron-domain
    geometry because lone pairs can compress the observable
    molecular bond angle.
    """

    if characteristic_bond_angle <= 0:
        raise ValueError(
            "Bond angle must be greater than zero."
        )

    # ========================================================
    # LINEAR
    # ========================================================

    if molecular_geometry == "linear":

        return get_ligand_positions(
            "linear",
            bonding_domains,
            lone_pair_domains
        )

    # ========================================================
    # TRIGONAL PLANAR
    # ========================================================

    if molecular_geometry == "trigonal_planar":

        return get_ligand_positions(
            "trigonal_planar",
            bonding_domains,
            lone_pair_domains
        )

    # ========================================================
    # TETRAHEDRAL
    # ========================================================

    if molecular_geometry == "tetrahedral":

        return get_ligand_positions(
            "tetrahedral",
            bonding_domains,
            lone_pair_domains
        )

    # ========================================================
    # TRIGONAL PYRAMIDAL
    # ========================================================

    if molecular_geometry == "trigonal_pyramidal":

        if bonding_domains != 3:
            raise ValueError(
                "Trigonal-pyramidal geometry requires "
                "exactly 3 bonding domains."
            )

        return _generate_three_pyramidal_positions(
            characteristic_bond_angle
        )

    # ========================================================
    # BENT
    # ========================================================

    if molecular_geometry == "bent":

        if bonding_domains != 2:
            raise ValueError(
                "Bent geometry requires exactly "
                "2 bonding domains."
            )

        return _generate_two_ligand_positions(
            characteristic_bond_angle
        )

    # ========================================================
    # TRIGONAL BIPYRAMIDAL
    # ========================================================

    if molecular_geometry == "trigonal_bipyramidal":

        return get_ligand_positions(
            "trigonal_bipyramidal",
            bonding_domains,
            lone_pair_domains
        )

    # ========================================================
    # OCTAHEDRAL
    # ========================================================

    if molecular_geometry == "octahedral":

        return get_ligand_positions(
            "octahedral",
            bonding_domains,
            lone_pair_domains
        )

    raise ValueError(
        f"Unsupported molecular geometry: "
        f"{molecular_geometry}"
    )

def get_ligand_atoms(
    atom_objects: dict,
    bonds: list,
    central_id: str
):
    """
    Return atom IDs directly bonded to the central atom.
    """

    ligand_atoms = []

    for bond in bonds:

        atom1 = bond["atom1"]
        atom2 = bond["atom2"]

        if atom1 == central_id:
            ligand_atoms.append(atom2)

        elif atom2 == central_id:
            ligand_atoms.append(atom1)

    return ligand_atoms

def analyze_chemistry(
    atoms,
    central_atom,
    charge=0
):
    """
    Run the chemistry core only:

        atoms
          ↓
        Lewis structure
          ↓
        VSEPR

    No bond-length or 3D calculation.
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

    for atom_id, atom_data in (
        lewis_result["atom_objects"].items()
    ):

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

    resonance_result = resolve_resonance(
        lewis_result["atom_objects"],
        lewis_result["bonds"],
        charge
    )

    # ========================================================
    # FINAL CHEMISTRY RESULT
    # ========================================================

    return {
        "lewis": lewis_result,
        "vsepr": vsepr_result,
        "ligand_atoms": ligand_atoms,
        "bond_lengths": bond_lengths,
        "coordinates": coordinates,
        "angle_validation": angle_validation,
        "resonance": resonance_result
    }

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
        lewis_result["bonds"],
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

    # ==================================================
    # DIATOMIC SPECIES
    # ==================================================
    #
    # A species with only one ligand has no molecular
    # bond angle to calculate. OH- is the current example.
    # Place the single ligand along +X and skip angle
    # validation for this case.
    # ==================================================

    if len(ligand_atoms) == 1:

        ligand_positions = [
            [1.0, 0.0, 0.0]
        ]

        angle_validation = {
            "expected_angle": None,
            "calculated_angles": [],
            "tolerance": 0.5,
            "invalid_angles": [],
            "valid": True,
            "reason": (
                "No bond angle exists for a diatomic species."
            )
        }

    else:

        ligand_positions = (
            generate_adjusted_ligand_positions(
                molecular_geometry,
                bonding_domains,
                characteristic_angle,
                vsepr_result["lone_pair_domains"]
            )
        )

        # ========================================================
        # STEP 9 — VALIDATE MOLECULAR ANGLES
        # ========================================================

        valid_angles = get_valid_molecular_angles(
            molecular_geometry
        )

        angle_validation = validate_molecular_angles(
            ligand_positions,
            valid_angles
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

    print()
    print("=" * 40)
    print("===== 3D BASIC TEST MATRIX =====")
    print("=" * 40)

    basic_cases = [
        {
            "name": "CO2",
            "atoms": {
                "C": 1,
                "O": 2
            },
            "central_atom": "C",
            "charge": 0
        },
        {
            "name": "BF3",
            "atoms": {
                "B": 1,
                "F": 3
            },
            "central_atom": "B",
            "charge": 0
        },
        {
            "name": "CH4",
            "atoms": {
                "C": 1,
                "H": 4
            },
            "central_atom": "C",
            "charge": 0
        },
        {
            "name": "NH3",
            "atoms": {
                "N": 1,
                "H": 3
            },
            "central_atom": "N",
            "charge": 0
        },
        {
            "name": "H2O",
            "atoms": {
                "O": 1,
                "H": 2
            },
            "central_atom": "O",
            "charge": 0
        }
    ]

    for case in basic_cases:

        print()
        print(case["name"])
        print("-" * 20)

        try:

            result = analyze_molecule(
                case["atoms"],
                case["central_atom"],
                case["charge"]
            )

            print(
                "Molecular geometry:",
                result["vsepr"]["molecular_geometry"]
            )

            print(
                "Characteristic angle:",
                result["vsepr"]["characteristic_bond_angle"]
            )

            print(
                "Bond lengths:",
                result["bond_lengths"]
            )

            print(
                "3D coordinates:"
            )

            for coordinate in result["coordinates"]:

                print(
                    coordinate
                )

            print(
                "Angle validation:",
                result["angle_validation"]["valid"]
            )

        except Exception as error:

            print(
                "ERROR:",
                error
            )

    # ============================================================
    # 3D ADVANCED TEST MATRIX
    # ============================================================

    print()
    print("=" * 40)
    print("===== 3D ADVANCED TEST MATRIX =====")
    print("=" * 40)


    advanced_cases = [
        {
            "name": "PCl5",
            "atoms": {
                "P": 1,
                "Cl": 5
            },
            "central_atom": "P",
            "charge": 0
        },
        {
            "name": "SF6",
            "atoms": {
                "S": 1,
                "F": 6
            },
            "central_atom": "S",
            "charge": 0
        }
    ]


    for case in advanced_cases:

        print()
        print(case["name"])
        print("-" * 20)

        try:

            result = analyze_molecule(
                case["atoms"],
                case["central_atom"],
                case["charge"]
            )

            print(
                "Molecular geometry:",
                result["vsepr"]["molecular_geometry"]
            )

            print(
                "Characteristic angle:",
                result["vsepr"]["characteristic_bond_angle"]
            )

            print(
                "Bond lengths:",
                result["bond_lengths"]
            )

            print(
                "3D coordinates:"
            )

            for coordinate in result["coordinates"]:

                print(
                    coordinate
                )

            print(
                "Angle validation:",
                result["angle_validation"]["valid"]
            )

        except Exception as error:

            print(
                "ERROR:",
                error
            )

    print()
print("=" * 40)
print("===== CHARGED ION TEST MATRIX =====")
print("=" * 40)

ION_TESTS = [
    {
        "name": "NH4+",
        "atoms": {"N": 1, "H": 4},
        "central_atom": "N",
        "charge": 1
    },
    {
        "name": "H3O+",
        "atoms": {"O": 1, "H": 3},
        "central_atom": "O",
        "charge": 1
    },
    {
        "name": "OH-",
        "atoms": {"O": 1, "H": 1},
        "central_atom": "O",
        "charge": -1
    }
]

for test in ION_TESTS:

    print()
    print(test["name"])
    print("-" * 20)

    try:

        result = analyze_molecule(
            test["atoms"],
            test["central_atom"],
            test["charge"]
        )

        print("Formula:", test["name"])

        print(
            "Formal charge:",
            result["lewis"]["total_formal_charge"]
        )

        print(
            "VSEPR:",
            result["vsepr"]["molecular_geometry"]
        )

        print(
            "Steric number:",
            result["vsepr"]["steric_number"]
        )

        print(
            "Characteristic angle:",
            result["vsepr"]["characteristic_bond_angle"]
        )

        print("PASS")

    except Exception as error:

        print("ERROR:", error)

        print()
    print("========================================")
    print("===== POLYATOMIC ION TEST MATRIX =====")
    print("========================================")

    polyatomic_ions = [
        ("NO3-", {"N": 1, "O": 3}, "N", -1),
        ("CO3^2-", {"C": 1, "O": 3}, "C", -2),
        ("SO4^2-", {"S": 1, "O": 4}, "S", -2),
        ("PO4^3-", {"P": 1, "O": 4}, "P", -3),
    ]

    for formula, atoms, central_atom, charge in polyatomic_ions:

        print()
        print(formula)
        print("--------------------")

        try:

            result = analyze_molecule(
                atoms,
                central_atom,
                charge
            )

            print("Resonance:")
            print(result["resonance"])

            print(
                "Formula:",
                formula
            )

            print(
                "Formal charge:",
                result["lewis"]["total_formal_charge"]
            )

            print(
                "VSEPR:",
                result["vsepr"]["molecular_geometry"]
            )

            print(
                "Steric number:",
                result["vsepr"]["steric_number"]
            )

            print(
                "Characteristic angle:",
                result["vsepr"]["characteristic_bond_angle"]
            )

            print("PASS")

        except Exception as error:

            print(
                "ERROR:",
                error
            )