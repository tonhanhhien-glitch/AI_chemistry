def count_electron_domains(
    atom_objects: dict,
    bonds: list,
    central_id: str
):
    """
    Count electron domains around the central atom.

    Rules:
    - Every bond counts as one electron domain.
    - Every lone pair counts as one electron domain.
    """

    bonding_domains = 0

    for bond in bonds:

        if (
            bond["atom1"] == central_id
            or bond["atom2"] == central_id
        ):
            bonding_domains += 1

    lone_electrons = (
        atom_objects[central_id]["lone_electrons"]
    )

    lone_pair_domains = (
        lone_electrons // 2
    )

    total_domains = (
        bonding_domains
        + lone_pair_domains
    )

    return {
        "bonding_domains": bonding_domains,
        "lone_pair_domains": lone_pair_domains,
        "total_domains": total_domains
    }

def calculate_steric_number(
    atom_objects: dict,
    bonds: list,
    central_id: str
):
    """
    Calculate the steric number of the central atom.

    Steric number =
    bonding electron domains
    + lone-pair domains.
    """

    domains = count_electron_domains(
        atom_objects,
        bonds,
        central_id
    )

    return domains["total_domains"]

def get_electron_geometry(
    steric_number: int
):
    """
    Determine electron-domain geometry
    from steric number.
    """

    geometry_map = {
        2: "linear",
        3: "trigonal_planar",
        4: "tetrahedral",
        5: "trigonal_bipyramidal",
        6: "octahedral"
    }

    return geometry_map.get(
        steric_number
    )

def get_molecular_geometry(
    steric_number: int,
    lone_pair_domains: int,
    bonding_domains: int
):
    """
    Determine molecular geometry from
    steric number, lone pairs, and bonding domains.
    """

    geometry_map = {
        (2, 0): "linear",

        (3, 0): "trigonal_planar",
        (3, 1): "bent",

        (4, 0): "tetrahedral",
        (4, 1): "trigonal_pyramidal",
        (4, 2): "bent",

        (5, 0): "trigonal_bipyramidal",
        (5, 1): "seesaw",
        (5, 2): "T-shaped",
        (5, 3): "linear",

        (6, 0): "octahedral",
        (6, 1): "square_pyramidal",
        (6, 2): "square_planar"
    }

    return geometry_map.get(
        (steric_number, lone_pair_domains)
    )

def get_ideal_bond_angle(
    steric_number: int
):
    """
    Return the ideal bond angle associated
    with the electron-domain geometry.
    """

    angle_map = {
        2: 180.0,
        3: 120.0,
        4: 109.5,
        5: 90.0,
        6: 90.0
    }

    return angle_map.get(
        steric_number
    )

def get_lone_pair_effect(
    steric_number: int,
    lone_pair_domains: int
):
    """
    Describe the effect of lone pairs on
    the molecular bond angles.
    """

    if lone_pair_domains == 0:
        return {
            "lone_pair_effect": "none",
            "angle_effect": "none"
        }

    if steric_number == 3 and lone_pair_domains == 1:
        return {
            "lone_pair_effect": "one_lone_pair",
            "angle_effect": "compressed"
        }

    if steric_number == 4 and lone_pair_domains == 1:
        return {
            "lone_pair_effect": "one_lone_pair",
            "angle_effect": "compressed"
        }

    if steric_number == 4 and lone_pair_domains == 2:
        return {
            "lone_pair_effect": "two_lone_pairs",
            "angle_effect": "strongly_compressed"
        }

    return {
        "lone_pair_effect": "present",
        "angle_effect": "compressed"
    }

def get_characteristic_bond_angle(
    steric_number: int,
    lone_pair_domains: int,
    molecular_geometry: str
):
    """
    Return the characteristic bond angle
    for common VSEPR geometries.
    """

    angle_map = {
        (2, 0, "linear"): 180.0,

        (3, 0, "trigonal_planar"): 120.0,
        (3, 1, "bent"): 118.0,

        (4, 0, "tetrahedral"): 109.5,
        (4, 1, "trigonal_pyramidal"): 107.0,
        (4, 2, "bent"): 104.5,

        (5, 0, "trigonal_bipyramidal"): 90.0,
        (5, 1, "seesaw"): 90.0,
        (5, 2, "T-shaped"): 90.0,
        (5, 3, "linear"): 180.0,

        (6, 0, "octahedral"): 90.0,
        (6, 1, "square_pyramidal"): 90.0,
        (6, 2, "square_planar"): 90.0
    }

    return angle_map.get(
        (
            steric_number,
            lone_pair_domains,
            molecular_geometry
        )
    )

def validate_vsepr_result(
    steric_number: int,
    bonding_domains: int,
    lone_pair_domains: int,
    electron_geometry: str,
    molecular_geometry: str,
    characteristic_angle
):
    """
    Validate the internal consistency of a VSEPR result.
    """

    # -----------------------------------------
    # Check domain count
    # -----------------------------------------

    domains_valid = (
        bonding_domains + lone_pair_domains
        == steric_number
    )

    # -----------------------------------------
    # Check electron geometry
    # -----------------------------------------

    expected_electron_geometry = (
        get_electron_geometry(
            steric_number
        )
    )

    electron_geometry_valid = (
        electron_geometry
        == expected_electron_geometry
    )

    # -----------------------------------------
    # Check molecular geometry
    # -----------------------------------------

    expected_molecular_geometry = (
        get_molecular_geometry(
            steric_number,
            lone_pair_domains,
            bonding_domains
        )
    )

    molecular_geometry_valid = (
        molecular_geometry
        == expected_molecular_geometry
    )

    # -----------------------------------------
    # Check bond angle exists
    # -----------------------------------------

    angle_valid = (
        characteristic_angle is not None
    )

    # -----------------------------------------
    # Overall validation
    # -----------------------------------------

    valid = (
        domains_valid
        and electron_geometry_valid
        and molecular_geometry_valid
        and angle_valid
    )

    return {
        "domains_valid": domains_valid,
        "electron_geometry_valid":
            electron_geometry_valid,
        "molecular_geometry_valid":
            molecular_geometry_valid,
        "angle_valid": angle_valid,
        "valid": valid
    }

def find_central_atom(
    atom_objects: dict,
    bonds: list
):
    """
    Find the atom connected to the greatest
    number of neighboring atoms.
    """

    bond_counts = {}

    for atom_id in atom_objects:
        bond_counts[atom_id] = 0

    for bond in bonds:

        bond_counts[
            bond["atom1"]
        ] += 1

        bond_counts[
            bond["atom2"]
        ] += 1

    central_id = max(
        bond_counts,
        key=bond_counts.get
    )

    return central_id

def analyze_vsepr(
    atom_objects: dict,
    bonds: list,
    central_id: str
):
    """
    Perform a complete VSEPR analysis
    from a final Lewis structure.
    """

    # -----------------------------------------
    # STEP 1: Electron domains
    # -----------------------------------------

    domains = count_electron_domains(
        atom_objects,
        bonds,
        central_id
    )

    bonding_domains = (
        domains["bonding_domains"]
    )

    lone_pair_domains = (
        domains["lone_pair_domains"]
    )

    total_domains = (
        domains["total_domains"]
    )

    # -----------------------------------------
    # STEP 2: Steric number
    # -----------------------------------------

    steric_number = (
        calculate_steric_number(
            atom_objects,
            bonds,
            central_id
        )
    )

    # -----------------------------------------
    # STEP 3: Electron geometry
    # -----------------------------------------

    electron_geometry = (
        get_electron_geometry(
            steric_number
        )
    )

    # -----------------------------------------
    # STEP 4: Molecular geometry
    # -----------------------------------------

    molecular_geometry = (
        get_molecular_geometry(
            steric_number,
            lone_pair_domains,
            bonding_domains
        )
    )

    # -----------------------------------------
    # STEP 5: Ideal bond angle
    # -----------------------------------------

    ideal_bond_angle = (
        get_ideal_bond_angle(
            steric_number
        )
    )

    # -----------------------------------------
    # STEP 6: Lone-pair effect
    # -----------------------------------------

    lone_pair_effect = (
        get_lone_pair_effect(
            steric_number,
            lone_pair_domains
        )
    )

    # -----------------------------------------
    # STEP 7: Characteristic angle
    # -----------------------------------------

    characteristic_bond_angle = (
        get_characteristic_bond_angle(
            steric_number,
            lone_pair_domains,
            molecular_geometry
        )
    )

    # -----------------------------------------
    # STEP 8: Validation
    # -----------------------------------------

    validation = validate_vsepr_result(
        steric_number,
        bonding_domains,
        lone_pair_domains,
        electron_geometry,
        molecular_geometry,
        characteristic_bond_angle
    )

    # -----------------------------------------
    # Final result
    # -----------------------------------------

    return {
        "central_atom": central_id,
        "bonding_domains": bonding_domains,
        "lone_pair_domains": lone_pair_domains,
        "total_domains": total_domains,
        "steric_number": steric_number,
        "electron_geometry": electron_geometry,
        "molecular_geometry": molecular_geometry,
        "ideal_bond_angle": ideal_bond_angle,
        "lone_pair_effect": lone_pair_effect,
        "characteristic_bond_angle":
            characteristic_bond_angle,
        "validation": validation
    }

if __name__ == "__main__":

    print(
        "===== VSEPR ENGINE : STEP 1 ====="
    )

    # ========================================
    # H2O SINGLE TEST
    # ========================================

    atom_objects = {
        "O1": {
            "symbol": "O",
            "bond_count": 2,
            "bonding_electrons": 4,
            "lone_electrons": 4,
            "octet": True
        },

        "H1": {
            "symbol": "H",
            "bond_count": 1,
            "bonding_electrons": 2,
            "lone_electrons": 0,
            "octet": True
        },

        "H2": {
            "symbol": "H",
            "bond_count": 1,
            "bonding_electrons": 2,
            "lone_electrons": 0,
            "octet": True
        }
    }

    bonds = [
        {
            "atom1": "O1",
            "atom2": "H1",
            "bond_order": 1
        },
        {
            "atom1": "O1",
            "atom2": "H2",
            "bond_order": 1
        }
    ]

    central_id = find_central_atom(
        atom_objects,
        bonds
    )

    print()
    print("Central atom:")
    print(central_id)

    domains = count_electron_domains(
        atom_objects,
        bonds,
        central_id
    )

    print()
    print("Electron domains:")
    print(domains)

    steric_number = calculate_steric_number(
        atom_objects,
        bonds,
        central_id
    )

    print()
    print("Steric number:")
    print(steric_number)

    electron_geometry = get_electron_geometry(
        steric_number
    )

    print()
    print("Electron geometry:")
    print(electron_geometry)

    molecular_geometry = get_molecular_geometry(
        steric_number,
        domains["lone_pair_domains"],
        domains["bonding_domains"]
    )

    print()
    print("Molecular geometry:")
    print(molecular_geometry)

    ideal_angle = get_ideal_bond_angle(
        steric_number
    )

    print()
    print("Ideal bond angle:")
    print(ideal_angle)

    lone_pair_effect = get_lone_pair_effect(
        steric_number,
        domains["lone_pair_domains"]
    )

    print()
    print("Lone pair effect:")
    print(lone_pair_effect)

    characteristic_angle = get_characteristic_bond_angle(
        steric_number,
        domains["lone_pair_domains"],
        molecular_geometry
    )

    print()
    print("Characteristic bond angle:")
    print(characteristic_angle)

    validation = validate_vsepr_result(
        steric_number,
        domains["bonding_domains"],
        domains["lone_pair_domains"],
        electron_geometry,
        molecular_geometry,
        characteristic_angle
    )

    print()
    print("VSEPR validation:")
    print(validation)

    vsepr_result = analyze_vsepr(
        atom_objects,
        bonds,
        central_id
    )

    print()
    print("===== COMPLETE VSEPR RESULT =====")
    print(vsepr_result)


    # ========================================
    # BASIC VSEPR TEST MATRIX
    # ========================================

    print()
    print("========================================")
    print("===== VSEPR TEST MATRIX : BASIC =====")
    print("========================================")

    test_cases = [

        # ------------------------------------
        # CO2
        # ------------------------------------

        {
            "name": "CO2",
            "central_id": "C1",

            "atom_objects": {
                "C1": {
                    "symbol": "C",
                    "bond_count": 2,
                    "bonding_electrons": 8,
                    "lone_electrons": 0,
                    "octet": True
                },

                "O1": {
                    "symbol": "O",
                    "bond_count": 1,
                    "bonding_electrons": 4,
                    "lone_electrons": 4,
                    "octet": True
                },

                "O2": {
                    "symbol": "O",
                    "bond_count": 1,
                    "bonding_electrons": 4,
                    "lone_electrons": 4,
                    "octet": True
                }
            },

            "bonds": [
                {
                    "atom1": "C1",
                    "atom2": "O1",
                    "bond_order": 2
                },
                {
                    "atom1": "C1",
                    "atom2": "O2",
                    "bond_order": 2
                }
            ]
        },


        # ------------------------------------
        # BF3
        # ------------------------------------

        {
            "name": "BF3",
            "central_id": "B1",

            "atom_objects": {
                "B1": {
                    "symbol": "B",
                    "bond_count": 3,
                    "bonding_electrons": 6,
                    "lone_electrons": 0,
                    "octet": True
                },

                "F1": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F2": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F3": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                }
            },

            "bonds": [
                {
                    "atom1": "B1",
                    "atom2": "F1",
                    "bond_order": 1
                },
                {
                    "atom1": "B1",
                    "atom2": "F2",
                    "bond_order": 1
                },
                {
                    "atom1": "B1",
                    "atom2": "F3",
                    "bond_order": 1
                }
            ]
        },


        # ------------------------------------
        # CH4
        # ------------------------------------

        {
            "name": "CH4",
            "central_id": "C1",

            "atom_objects": {
                "C1": {
                    "symbol": "C",
                    "bond_count": 4,
                    "bonding_electrons": 8,
                    "lone_electrons": 0,
                    "octet": True
                },

                "H1": {
                    "symbol": "H",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 0,
                    "octet": True
                },

                "H2": {
                    "symbol": "H",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 0,
                    "octet": True
                },

                "H3": {
                    "symbol": "H",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 0,
                    "octet": True
                },

                "H4": {
                    "symbol": "H",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 0,
                    "octet": True
                }
            },

            "bonds": [
                {
                    "atom1": "C1",
                    "atom2": "H1",
                    "bond_order": 1
                },
                {
                    "atom1": "C1",
                    "atom2": "H2",
                    "bond_order": 1
                },
                {
                    "atom1": "C1",
                    "atom2": "H3",
                    "bond_order": 1
                },
                {
                    "atom1": "C1",
                    "atom2": "H4",
                    "bond_order": 1
                }
            ]
        },


        # ------------------------------------
        # NH3
        # ------------------------------------

        {
            "name": "NH3",
            "central_id": "N1",

            "atom_objects": {
                "N1": {
                    "symbol": "N",
                    "bond_count": 3,
                    "bonding_electrons": 6,
                    "lone_electrons": 2,
                    "octet": True
                },

                "H1": {
                    "symbol": "H",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 0,
                    "octet": True
                },

                "H2": {
                    "symbol": "H",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 0,
                    "octet": True
                },

                "H3": {
                    "symbol": "H",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 0,
                    "octet": True
                }
            },

            "bonds": [
                {
                    "atom1": "N1",
                    "atom2": "H1",
                    "bond_order": 1
                },
                {
                    "atom1": "N1",
                    "atom2": "H2",
                    "bond_order": 1
                },
                {
                    "atom1": "N1",
                    "atom2": "H3",
                    "bond_order": 1
                }
            ]
        },


        # ------------------------------------
        # H2O
        # ------------------------------------

        {
            "name": "H2O",
            "central_id": "O1",

            "atom_objects": {
                "O1": {
                    "symbol": "O",
                    "bond_count": 2,
                    "bonding_electrons": 4,
                    "lone_electrons": 4,
                    "octet": True
                },

                "H1": {
                    "symbol": "H",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 0,
                    "octet": True
                },

                "H2": {
                    "symbol": "H",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 0,
                    "octet": True
                }
            },

            "bonds": [
                {
                    "atom1": "O1",
                    "atom2": "H1",
                    "bond_order": 1
                },
                {
                    "atom1": "O1",
                    "atom2": "H2",
                    "bond_order": 1
                }
            ]
        }
    ]


    # ========================================
    # RUN BASIC MATRIX
    # ========================================

    for case in test_cases:

        result = analyze_vsepr(
            case["atom_objects"],
            case["bonds"],
            case["central_id"]
        )

        print()
        print(case["name"])
        print("--------------------")

        print(
            "Central:",
            result["central_atom"]
        )

        print(
            "Steric number:",
            result["steric_number"]
        )

        print(
            "Electron geometry:",
            result["electron_geometry"]
        )

        print(
            "Molecular geometry:",
            result["molecular_geometry"]
        )

        print(
            "Bond angle:",
            result["characteristic_bond_angle"]
        )

        print(
            "Valid:",
            result["validation"]["valid"]
        )


    # ========================================
    # ADVANCED VSEPR TEST MATRIX
    # ========================================

    print()
    print("========================================")
    print("===== VSEPR TEST MATRIX : ADVANCED ====")
    print("========================================")

    advanced_cases = [

        # ------------------------------------
        # PCl5
        # ------------------------------------

        {
            "name": "PCl5",
            "central_id": "P1",

            "atom_objects": {
                "P1": {
                    "symbol": "P",
                    "bond_count": 5,
                    "bonding_electrons": 10,
                    "lone_electrons": 0,
                    "octet": True
                },

                "Cl1": {
                    "symbol": "Cl",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "Cl2": {
                    "symbol": "Cl",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "Cl3": {
                    "symbol": "Cl",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "Cl4": {
                    "symbol": "Cl",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "Cl5": {
                    "symbol": "Cl",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                }
            },

            "bonds": [
                {
                    "atom1": "P1",
                    "atom2": "Cl1",
                    "bond_order": 1
                },
                {
                    "atom1": "P1",
                    "atom2": "Cl2",
                    "bond_order": 1
                },
                {
                    "atom1": "P1",
                    "atom2": "Cl3",
                    "bond_order": 1
                },
                {
                    "atom1": "P1",
                    "atom2": "Cl4",
                    "bond_order": 1
                },
                {
                    "atom1": "P1",
                    "atom2": "Cl5",
                    "bond_order": 1
                }
            ]
        },


        # ------------------------------------
        # SF4
        # ------------------------------------

        {
            "name": "SF4",
            "central_id": "S1",

            "atom_objects": {
                "S1": {
                    "symbol": "S",
                    "bond_count": 4,
                    "bonding_electrons": 8,
                    "lone_electrons": 2,
                    "octet": True
                },

                "F1": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F2": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F3": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F4": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                }
            },

            "bonds": [
                {
                    "atom1": "S1",
                    "atom2": "F1",
                    "bond_order": 1
                },
                {
                    "atom1": "S1",
                    "atom2": "F2",
                    "bond_order": 1
                },
                {
                    "atom1": "S1",
                    "atom2": "F3",
                    "bond_order": 1
                },
                {
                    "atom1": "S1",
                    "atom2": "F4",
                    "bond_order": 1
                }
            ]
        },


        # ------------------------------------
        # ClF3
        # ------------------------------------

        {
            "name": "ClF3",
            "central_id": "Cl1",

            "atom_objects": {
                "Cl1": {
                    "symbol": "Cl",
                    "bond_count": 3,
                    "bonding_electrons": 6,
                    "lone_electrons": 4,
                    "octet": True
                },

                "F1": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F2": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F3": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                }
            },

            "bonds": [
                {
                    "atom1": "Cl1",
                    "atom2": "F1",
                    "bond_order": 1
                },
                {
                    "atom1": "Cl1",
                    "atom2": "F2",
                    "bond_order": 1
                },
                {
                    "atom1": "Cl1",
                    "atom2": "F3",
                    "bond_order": 1
                }
            ]
        },


        # ------------------------------------
        # XeF2
        # ------------------------------------

        {
            "name": "XeF2",
            "central_id": "Xe1",

            "atom_objects": {
                "Xe1": {
                    "symbol": "Xe",
                    "bond_count": 2,
                    "bonding_electrons": 4,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F1": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F2": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                }
            },

            "bonds": [
                {
                    "atom1": "Xe1",
                    "atom2": "F1",
                    "bond_order": 1
                },
                {
                    "atom1": "Xe1",
                    "atom2": "F2",
                    "bond_order": 1
                }
            ]
        },


        # ------------------------------------
        # SF6
        # ------------------------------------

        {
            "name": "SF6",
            "central_id": "S1",

            "atom_objects": {
                "S1": {
                    "symbol": "S",
                    "bond_count": 6,
                    "bonding_electrons": 12,
                    "lone_electrons": 0,
                    "octet": True
                },

                "F1": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F2": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F3": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F4": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F5": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F6": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                }
            },

            "bonds": [
                {
                    "atom1": "S1",
                    "atom2": "F1",
                    "bond_order": 1
                },
                {
                    "atom1": "S1",
                    "atom2": "F2",
                    "bond_order": 1
                },
                {
                    "atom1": "S1",
                    "atom2": "F3",
                    "bond_order": 1
                },
                {
                    "atom1": "S1",
                    "atom2": "F4",
                    "bond_order": 1
                },
                {
                    "atom1": "S1",
                    "atom2": "F5",
                    "bond_order": 1
                },
                {
                    "atom1": "S1",
                    "atom2": "F6",
                    "bond_order": 1
                }
            ]
        },


        # ------------------------------------
        # BrF5
        # ------------------------------------

        {
            "name": "BrF5",
            "central_id": "Br1",

            "atom_objects": {
                "Br1": {
                    "symbol": "Br",
                    "bond_count": 5,
                    "bonding_electrons": 10,
                    "lone_electrons": 2,
                    "octet": True
                },

                "F1": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F2": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F3": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F4": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F5": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                }
            },

            "bonds": [
                {
                    "atom1": "Br1",
                    "atom2": "F1",
                    "bond_order": 1
                },
                {
                    "atom1": "Br1",
                    "atom2": "F2",
                    "bond_order": 1
                },
                {
                    "atom1": "Br1",
                    "atom2": "F3",
                    "bond_order": 1
                },
                {
                    "atom1": "Br1",
                    "atom2": "F4",
                    "bond_order": 1
                },
                {
                    "atom1": "Br1",
                    "atom2": "F5",
                    "bond_order": 1
                }
            ]
        },


        # ------------------------------------
        # XeF4
        # ------------------------------------

        {
            "name": "XeF4",
            "central_id": "Xe1",

            "atom_objects": {
                "Xe1": {
                    "symbol": "Xe",
                    "bond_count": 4,
                    "bonding_electrons": 8,
                    "lone_electrons": 4,
                    "octet": True
                },

                "F1": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F2": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F3": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                },

                "F4": {
                    "symbol": "F",
                    "bond_count": 1,
                    "bonding_electrons": 2,
                    "lone_electrons": 6,
                    "octet": True
                }
            },

            "bonds": [
                {
                    "atom1": "Xe1",
                    "atom2": "F1",
                    "bond_order": 1
                },
                {
                    "atom1": "Xe1",
                    "atom2": "F2",
                    "bond_order": 1
                },
                {
                    "atom1": "Xe1",
                    "atom2": "F3",
                    "bond_order": 1
                },
                {
                    "atom1": "Xe1",
                    "atom2": "F4",
                    "bond_order": 1
                }
            ]
        }
    ]


    # ========================================
    # RUN ADVANCED MATRIX
    # ========================================

    for case in advanced_cases:

        result = analyze_vsepr(
            case["atom_objects"],
            case["bonds"],
            case["central_id"]
        )

        print()
        print(case["name"])
        print("--------------------")

        print(
            "Central:",
            result["central_atom"]
        )

        print(
            "Steric number:",
            result["steric_number"]
        )

        print(
            "Electron geometry:",
            result["electron_geometry"]
        )

        print(
            "Molecular geometry:",
            result["molecular_geometry"]
        )

        print(
            "Lone pairs:",
            result["lone_pair_domains"]
        )

        print(
            "Bond angle:",
            result["characteristic_bond_angle"]
        )

        print(
            "Valid:",
            result["validation"]["valid"]
        )