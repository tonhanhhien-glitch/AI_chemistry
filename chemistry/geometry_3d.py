"""
3D Geometry Engine

Converts VSEPR molecular geometry into
idealized 3D spatial templates.

This module currently contains geometry templates only.
Molecular-specific bond lengths and experimental coordinates
will be added later.
"""


GEOMETRY_TEMPLATES = {

    "linear": {
        "steric_number": 2,
        "coordination_number": 2,
        "ideal_angles": [180.0],
        "positions": [
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0]
        ]
    },

    "trigonal_planar": {
        "steric_number": 3,
        "coordination_number": 3,
        "ideal_angles": [120.0],
        "positions": [
            [1.0, 0.0, 0.0],
            [-0.5, 0.8660254, 0.0],
            [-0.5, -0.8660254, 0.0]
        ]
    },

    "tetrahedral": {
        "steric_number": 4,
        "coordination_number": 4,
        "ideal_angles": [109.5],
        "positions": [
            [1.0, 1.0, 1.0],
            [1.0, -1.0, -1.0],
            [-1.0, 1.0, -1.0],
            [-1.0, -1.0, 1.0]
        ]
    },

    "trigonal_bipyramidal": {
        "steric_number": 5,
        "coordination_number": 5,
        "ideal_angles": [
            90.0,
            120.0,
            180.0
        ],
        "positions": [
            [0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0],
            [1.0, 0.0, 0.0],
            [-0.5, 0.8660254, 0.0],
            [-0.5, -0.8660254, 0.0]
        ]
    },

    "octahedral": {
        "steric_number": 6,
        "coordination_number": 6,
        "ideal_angles": [
            90.0,
            180.0
        ],
        "positions": [
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, -1.0, 0.0],
            [0.0, 0.0, 1.0],
            [0.0, 0.0, -1.0]
        ]
    }
}


def get_geometry_template(
    geometry: str
):
    """
    Return the 3D template for a VSEPR
    electron or molecular geometry.
    """

    template = GEOMETRY_TEMPLATES.get(
        geometry
    )

    if template is None:

        raise ValueError(
            f"Unsupported 3D geometry: {geometry}"
        )

    return template


def get_geometry_positions(
    geometry: str
):
    """
    Return idealized 3D positions
    for a geometry.
    """

    template = get_geometry_template(
        geometry
    )

    return template["positions"]


def get_ideal_angles(
    geometry: str
):
    """
    Return idealized bond angles
    associated with a geometry.
    """

    template = get_geometry_template(
        geometry
    )

    return template["ideal_angles"]


def validate_geometry_template(
    geometry: str
):
    """
    Validate the internal consistency of
    a geometry template.
    """

    template = get_geometry_template(
        geometry
    )

    positions = template["positions"]

    coordination_number = (
        template["coordination_number"]
    )

    if len(positions) != coordination_number:

        return False

    if template["steric_number"] < (
        coordination_number
    ):

        return False

    return True

import math


def calculate_vector_angle(
    vector1: list,
    vector2: list
):
    """
    Calculate the angle between two 3D vectors
    in degrees.
    """

    dot_product = sum(
        a * b
        for a, b in zip(vector1, vector2)
    )

    magnitude1 = math.sqrt(
        sum(
            value ** 2
            for value in vector1
        )
    )

    magnitude2 = math.sqrt(
        sum(
            value ** 2
            for value in vector2
        )
    )

    if magnitude1 == 0 or magnitude2 == 0:

        raise ValueError(
            "Zero-length vector is not allowed."
        )

    cosine_value = (
        dot_product
        / (magnitude1 * magnitude2)
    )

    # Protect against floating-point errors.
    cosine_value = max(
        -1.0,
        min(1.0, cosine_value)
    )

    angle = math.degrees(
        math.acos(cosine_value)
    )

    return angle


def calculate_all_pairwise_angles(
    positions: list
):
    """
    Calculate every unique pairwise angle
    between 3D positions.
    """

    angles = []

    for i in range(len(positions)):

        for j in range(
            i + 1,
            len(positions)
        ):

            angle = calculate_vector_angle(
                positions[i],
                positions[j]
            )

            angles.append({
                "position_1": i,
                "position_2": j,
                "angle": round(
                    angle,
                    4
                )
            })

    return angles


def validate_geometry_angles(
    geometry: str,
    tolerance: float = 0.5
):
    """
    Validate whether the 3D template positions
    produce chemically expected ideal angles.
    """

    template = get_geometry_template(
        geometry
    )

    positions = template["positions"]

    calculated_angles = (
        calculate_all_pairwise_angles(
            positions
        )
    )

    expected_angles = template[
        "ideal_angles"
    ]

    invalid_angles = []

    for result in calculated_angles:

        actual_angle = result["angle"]

        matches = any(
            abs(
                actual_angle
                - expected_angle
            ) <= tolerance
            for expected_angle
            in expected_angles
        )

        if not matches:

            invalid_angles.append(
                result
            )

    return {
        "geometry": geometry,
        "expected_angles": expected_angles,
        "calculated_angles": calculated_angles,
        "tolerance": tolerance,
        "invalid_angles": invalid_angles,
        "valid": len(
            invalid_angles
        ) == 0
    }

def normalize_vector(vector: list):
    """
    Convert a vector into a unit vector.
    """

    magnitude = math.sqrt(
        sum(
            value ** 2
            for value in vector
        )
    )

    if magnitude == 0:

        raise ValueError(
            "Cannot normalize a zero-length vector."
        )

    return [
        value / magnitude
        for value in vector
    ]


def scale_vector(
    vector: list,
    distance: float
):
    """
    Scale a unit direction vector
    to the requested bond length.
    """

    if distance <= 0:

        raise ValueError(
            "Bond length must be greater than zero."
        )

    unit_vector = normalize_vector(
        vector
    )

    return [
        value * distance
        for value in unit_vector
    ]


def generate_coordinates(
    geometry: str,
    bond_lengths: list,
    central_coordinate: list = None
):
    """
    Generate idealized 3D coordinates
    from a geometry template and bond lengths.

    bond_lengths must contain one distance
    for each ligand position.
    """

    template = get_geometry_template(
        geometry
    )

    positions = template["positions"]

    if len(bond_lengths) != len(positions):

        raise ValueError(
            "Number of bond lengths must match "
            "the number of geometry positions."
        )

    if central_coordinate is None:

        central_coordinate = [
            0.0,
            0.0,
            0.0
        ]

    if len(central_coordinate) != 3:

        raise ValueError(
            "Central coordinate must contain "
            "exactly three values."
        )

    coordinates = []

    coordinates.append({
        "atom_index": 0,
        "coordinate": central_coordinate
    })

    for index, (
        direction,
        bond_length
    ) in enumerate(
        zip(
            positions,
            bond_lengths
        ),
        start=1
    ):

        displacement = scale_vector(
            direction,
            bond_length
        )

        coordinate = [
            central_coordinate[i]
            + displacement[i]
            for i in range(3)
        ]

        coordinates.append({
            "atom_index": index,
            "coordinate": coordinate
        })

    return coordinates


def calculate_distance(
    coordinate1: list,
    coordinate2: list
):
    """
    Calculate Euclidean distance between
    two 3D coordinates.
    """

    return math.sqrt(
        sum(
            (
                coordinate1[i]
                - coordinate2[i]
            ) ** 2
            for i in range(3)
        )
    )


def validate_coordinates(
    coordinates: list,
    expected_bond_lengths: list,
    tolerance: float = 0.001
):
    """
    Validate generated coordinates against
    expected bond lengths.
    """

    if len(coordinates) != (
        len(expected_bond_lengths) + 1
    ):

        return {
            "valid": False,
            "reason": (
                "Coordinate count does not "
                "match expected bond count."
            )
        }

    central = coordinates[0][
        "coordinate"
    ]

    calculated_distances = []
    invalid_distances = []

    for index, expected in enumerate(
        expected_bond_lengths,
        start=1
    ):

        ligand = coordinates[index][
            "coordinate"
        ]

        actual = calculate_distance(
            central,
            ligand
        )

        actual = round(
            actual,
            4
        )

        calculated_distances.append(
            actual
        )

        if abs(
            actual - expected
        ) > tolerance:

            invalid_distances.append({
                "atom_index": index,
                "expected": expected,
                "actual": actual
            })

    return {
        "expected_distances":
            expected_bond_lengths,
        "calculated_distances":
            calculated_distances,
        "tolerance":
            tolerance,
        "invalid_distances":
            invalid_distances,
        "valid":
            len(invalid_distances) == 0
    }

def get_ligand_positions(
    geometry: str,
    bonding_domains: int,
    lone_pair_domains: int
):
    """
    Select the 3D positions occupied by bonded atoms.

    The geometry template describes electron-domain
    positions. Lone-pair positions are removed from
    the molecular geometry.

    This function currently uses idealized positional
    conventions for VSEPR.
    """

    template = get_geometry_template(
        geometry
    )

    positions = template["positions"]

    total_domains = len(positions)

    if (
        bonding_domains
        + lone_pair_domains
        != total_domains
    ):

        raise ValueError(
            "Bonding domains + lone-pair domains "
            "must equal the template coordination "
            "positions."
        )

    if bonding_domains < 0:

        raise ValueError(
            "Bonding domains cannot be negative."
        )

    if lone_pair_domains < 0:

        raise ValueError(
            "Lone-pair domains cannot be negative."
        )

    if bonding_domains > total_domains:

        raise ValueError(
            "Bonding domains exceed available "
            "geometry positions."
        )

    # --------------------------------------------------
    # Position-selection rules
    # --------------------------------------------------

    if geometry == "linear":

        ligand_positions = positions[
            :bonding_domains
        ]

    elif geometry == "trigonal_planar":

        ligand_positions = positions[
            :bonding_domains
        ]

    elif geometry == "tetrahedral":

        ligand_positions = positions[
            :bonding_domains
        ]

    elif geometry == "trigonal_bipyramidal":

        if lone_pair_domains == 0:

            ligand_positions = positions

        elif lone_pair_domains == 1:

            # One lone pair prefers an equatorial
            # position in a trigonal bipyramidal
            # electron-domain arrangement.
            ligand_positions = [
                positions[0],
                positions[1],
                positions[3],
                positions[4]
            ]

        elif lone_pair_domains == 2:

            # Two lone pairs occupy equatorial
            # positions.
            ligand_positions = [
                positions[0],
                positions[1],
                positions[2]
            ]

        elif lone_pair_domains == 3:

            # Three lone pairs occupy all three
            # equatorial positions, leaving the two
            # axial positions for bonded atoms.
            ligand_positions = [
                positions[0],
                positions[1]
            ]

        else:

            raise ValueError(
                "Unsupported lone-pair count "
                "for trigonal bipyramidal geometry."
            )

    elif geometry == "octahedral":

        # For the first stage, use a consistent
        # idealized positional convention.
        ligand_positions = positions[
            :bonding_domains
        ]

    else:

        raise ValueError(
            f"Unsupported geometry: {geometry}"
        )

    if len(ligand_positions) != bonding_domains:

        raise ValueError(
            "Generated ligand position count "
            "does not match bonding domains."
        )

    return ligand_positions

def generate_molecular_coordinates(
    geometry: str,
    bonding_domains: int,
    lone_pair_domains: int,
    bond_lengths: list,
    central_coordinate: list = None
):
    """
    Generate 3D coordinates for the central atom
    and bonded atoms only.

    Lone pairs influence position selection but
    are not represented as atoms in the molecular
    coordinate output.
    """

    ligand_positions = get_ligand_positions(
        geometry,
        bonding_domains,
        lone_pair_domains
    )

    if len(bond_lengths) != bonding_domains:

        raise ValueError(
            "Number of bond lengths must equal "
            "the number of bonding domains."
        )

    if central_coordinate is None:

        central_coordinate = [
            0.0,
            0.0,
            0.0
        ]

    coordinates = [
        {
            "atom_index": 0,
            "role": "central",
            "coordinate": central_coordinate
        }
    ]

    for index, (
        direction,
        bond_length
    ) in enumerate(
        zip(
            ligand_positions,
            bond_lengths
        ),
        start=1
    ):

        displacement = scale_vector(
            direction,
            bond_length
        )

        coordinate = [
            central_coordinate[i]
            + displacement[i]
            for i in range(3)
        ]

        coordinates.append({
            "atom_index": index,
            "role": "ligand",
            "coordinate": coordinate
        })

    return coordinates

def rotate_vector_around_z(
    vector: list,
    angle_degrees: float
):
    """
    Rotate a 3D vector around the z-axis.
    """

    angle_radians = math.radians(
        angle_degrees
    )

    cosine = math.cos(
        angle_radians
    )

    sine = math.sin(
        angle_radians
    )

    x = vector[0]
    y = vector[1]
    z = vector[2]

    return [
        x * cosine - y * sine,
        x * sine + y * cosine,
        z
    ]


def generate_planar_positions(
    bonding_domains: int,
    bond_angle: float
):
    """
    Generate equally distributed ligand directions
    in a plane.

    This is mainly used for linear and
    trigonal-planar molecular arrangements.
    """

    if bonding_domains < 1:

        raise ValueError(
            "Bonding domains must be at least 1."
        )

    if bonding_domains == 1:

        return [
            [1.0, 0.0, 0.0]
        ]

    if bonding_domains == 2:

        if abs(
            bond_angle - 180.0
        ) > 0.001:

            raise ValueError(
                "Two ligand planar geometry "
                "requires a 180 degree angle."
            )

        return [
            [1.0, 0.0, 0.0],
            [-1.0, 0.0, 0.0]
        ]

    if bonding_domains == 3:

        if abs(
            bond_angle - 120.0
        ) > 0.001:

            raise ValueError(
                "Three equally distributed "
                "planar ligands require 120 degrees."
            )

        return [
            [1.0, 0.0, 0.0],
            [
                -0.5,
                math.sqrt(3) / 2,
                0.0
            ],
            [
                -0.5,
                -math.sqrt(3) / 2,
                0.0
            ]
        ]

    raise ValueError(
        "Unsupported planar ligand count."
    )


def generate_tetrahedral_ligand_positions(
    bonding_domains: int,
    bond_angle: float
):
    """
    Generate idealized tetrahedral ligand
    directions for 1-4 bonded atoms.

    For four ligands, the tetrahedral angle
    is determined geometrically.

    For fewer ligands, selected positions
    represent molecular geometries derived
    from tetrahedral electron domains.
    """

    if bonding_domains < 1:

        raise ValueError(
            "Bonding domains must be at least 1."
        )

    if bonding_domains > 4:

        raise ValueError(
            "Tetrahedral geometry supports "
            "at most 4 bonding domains."
        )

    ideal_angle = math.degrees(
        math.acos(-1.0 / 3.0)
    )

    if bonding_domains == 4:

        if abs(
            bond_angle - ideal_angle
        ) > 0.5:

            raise ValueError(
                "Four tetrahedral ligands require "
                "approximately 109.47 degrees."
            )

        return [
            [
                1.0,
                1.0,
                1.0
            ],
            [
                1.0,
                -1.0,
                -1.0
            ],
            [
                -1.0,
                1.0,
                -1.0
            ],
            [
                -1.0,
                -1.0,
                1.0
            ]
        ]

    if bonding_domains == 3:

        # Trigonal-pyramidal arrangement.
        #
        # Generate three ligand vectors with
        # exactly the requested pairwise angle.

        angle_radians = math.radians(
            bond_angle
        )

        cosine_angle = math.cos(
            angle_radians
        )

        z_squared = (
            2.0 * cosine_angle + 1.0
        ) / 3.0

        if z_squared < 0.0 or z_squared > 1.0:

            raise ValueError(
                "Invalid bond angle for "
                "trigonal-pyramidal geometry."
            )

        z_component = math.sqrt(
            z_squared
        )

        radial_component = math.sqrt(
            1.0 - z_squared
        )

        positions = []

        for azimuth_degrees in [
            0.0,
            120.0,
            240.0
        ]:

            azimuth_radians = math.radians(
                azimuth_degrees
            )

            positions.append([
                radial_component
                * math.cos(
                    azimuth_radians
                ),

                radial_component
                * math.sin(
                    azimuth_radians
                ),

                z_component
            ])

        return positions

    if bonding_domains == 2:

        # Bent geometry is handled separately
        # by the molecular-angle adjustment
        # layer.

        half_angle = (
            bond_angle / 2.0
        )

        angle_radians = math.radians(
            half_angle
        )

        return [
            [
                math.cos(angle_radians),
                math.sin(angle_radians),
                0.0
            ],
            [
                math.cos(angle_radians),
                -math.sin(angle_radians),
                0.0
            ]
        ]

    return [
        normalize_vector(
            [
                1.0,
                1.0,
                1.0
            ]
        )
    ]


def generate_adjusted_ligand_positions(
    molecular_geometry: str,
    bonding_domains: int,
    characteristic_bond_angle: float
):
    """
    Generate ligand directions based on
    molecular geometry and characteristic
    bond angle.

    This layer is intentionally separate from
    the electron-domain geometry templates.
    """

    if characteristic_bond_angle <= 0:

        raise ValueError(
            "Bond angle must be greater than zero."
        )

    if molecular_geometry == "linear":

        return generate_planar_positions(
            bonding_domains,
            180.0
        )

    if molecular_geometry == "trigonal_planar":

        return generate_planar_positions(
            bonding_domains,
            120.0
        )

    if molecular_geometry == "tetrahedral":

        return generate_tetrahedral_ligand_positions(
            bonding_domains,
            characteristic_bond_angle
        )

    if molecular_geometry == "trigonal_pyramidal":

        return generate_tetrahedral_ligand_positions(
            bonding_domains,
            characteristic_bond_angle
        )

    if molecular_geometry == "bent":

        return generate_tetrahedral_ligand_positions(
            bonding_domains,
            characteristic_bond_angle
        )

    raise ValueError(
        f"Unsupported molecular geometry: "
        f"{molecular_geometry}"
    )


def calculate_angle(
    vector1: list,
    vector2: list
):
    """
    Calculate the angle in degrees between
    two 3D vectors.
    """

    # Accept either a raw [x, y, z] vector
    # or a coordinate record containing
    # {"coordinate": [x, y, z]}.
    if isinstance(vector1, dict):

        if "coordinate" not in vector1:
            raise ValueError(
                "Vector1 dictionary must contain "
                "'coordinate'."
            )

        vector1 = vector1["coordinate"]

    if isinstance(vector2, dict):

        if "coordinate" not in vector2:
            raise ValueError(
                "Vector2 dictionary must contain "
                "'coordinate'."
            )

        vector2 = vector2["coordinate"]

    if len(vector1) != 3:

        raise ValueError(
            "Vector1 must contain exactly "
            "three values."
        )

    if len(vector2) != 3:

        raise ValueError(
            "Vector2 must contain exactly "
            "three values."
        )

    try:

        vector1 = [
            float(value)
            for value in vector1
        ]

        vector2 = [
            float(value)
            for value in vector2
        ]

    except (TypeError, ValueError):

        raise ValueError(
            "Vector coordinates must be numeric."
        )

    magnitude1 = math.sqrt(
        sum(
            value ** 2
            for value in vector1
        )
    )

    magnitude2 = math.sqrt(
        sum(
            value ** 2
            for value in vector2
        )
    )

    if magnitude1 == 0:

        raise ValueError(
            "Vector1 cannot be a zero vector."
        )

    if magnitude2 == 0:

        raise ValueError(
            "Vector2 cannot be a zero vector."
        )

    dot_product = sum(
        vector1[i] * vector2[i]
        for i in range(3)
    )

    cosine = (
        dot_product
        / (magnitude1 * magnitude2)
    )

    cosine = max(
        -1.0,
        min(1.0, cosine)
    )

    angle = math.degrees(
        math.acos(cosine)
    )

    return angle


def calculate_ligand_angles(
    positions: list
):
    """
    Calculate all pairwise angles between
    ligand direction vectors.
    """

    calculated_angles = []

    for i in range(len(positions)):

        for j in range(
            i + 1,
            len(positions)
        ):

            angle = calculate_angle(
                positions[i],
                positions[j]
            )

            calculated_angles.append({
                "position_1": i,
                "position_2": j,
                "angle": round(
                    angle,
                    4
                )
            })

    return calculated_angles


def validate_molecular_angles(
    positions: list,
    expected_angle: float,
    tolerance: float = 0.5
):
    """
    Validate all molecular bond angles
    against the expected characteristic angle.
    """

    if expected_angle <= 0:

        raise ValueError(
            "Expected bond angle must be "
            "greater than zero."
        )

    calculated_angles = (
        calculate_ligand_angles(
            positions
        )
    )

    invalid_angles = []

    for result in calculated_angles:

        difference = abs(
            result["angle"]
            - expected_angle
        )

        if difference > tolerance:

            invalid_angles.append({
                "position_1":
                    result["position_1"],

                "position_2":
                    result["position_2"],

                "expected":
                    expected_angle,

                "actual":
                    result["angle"],

                "difference":
                    round(
                        difference,
                        4
                    )
            })

    return {
        "expected_angle":
            expected_angle,

        "calculated_angles":
            calculated_angles,

        "tolerance":
            tolerance,

        "invalid_angles":
            invalid_angles,

        "valid":
            len(invalid_angles) == 0
    }


if __name__ == "__main__":

    print(
        "===== 3D GEOMETRY ENGINE ====="
    )

    # ==================================================
    # BASIC GEOMETRY TEMPLATE TEST
    # ==================================================

    for geometry in GEOMETRY_TEMPLATES:

        template = get_geometry_template(
            geometry
        )

        print()
        print(geometry)
        print("--------------------")

        print(
            "Steric number:",
            template["steric_number"]
        )

        print(
            "Coordination number:",
            template["coordination_number"]
        )

        print(
            "Ideal angles:",
            template["ideal_angles"]
        )

        print(
            "Positions:"
        )

        for position in template[
            "positions"
        ]:

            print(position)

        template_valid = (
            validate_geometry_template(
                geometry
            )
        )

        print(
            "Template valid:",
            template_valid
        )

        angle_validation = (
            validate_geometry_angles(
                geometry
            )
        )

        print(
            "Calculated angles:"
        )

        for angle in (
            angle_validation[
                "calculated_angles"
            ]
        ):

            print(angle)

        print(
            "Angle validation:",
            angle_validation["valid"]
        )

    # ==================================================
    # COORDINATE GENERATOR TEST
    # ==================================================

    print()
    print(
        "========================================"
    )
    print(
        "===== COORDINATE GENERATOR TEST ====="
    )
    print(
        "========================================"
    )

    coordinate_test_cases = [

        {
            "name": "CO2",
            "geometry": "linear",
            "bond_lengths": [
                1.16,
                1.16
            ]
        },

        {
            "name": "CH4",
            "geometry": "tetrahedral",
            "bond_lengths": [
                1.09,
                1.09,
                1.09,
                1.09
            ]
        },

        {
            "name": "Tetrahedral Test",
            "geometry": "tetrahedral",
            "bond_lengths": [
                1.00,
                1.00,
                1.00,
                1.00
            ]
        }
    ]

    for case in coordinate_test_cases:

        print()
        print(
            case["name"]
        )

        print(
            "--------------------"
        )

        coordinates = generate_coordinates(
            case["geometry"],
            case["bond_lengths"]
        )

        print(
            "Coordinates:"
        )

        for atom in coordinates:

            print(
                atom
            )

        validation = (
            validate_coordinates(
                coordinates,
                case["bond_lengths"]
            )
        )

        print(
            "Expected distances:",
            validation[
                "expected_distances"
            ]
        )

        print(
            "Calculated distances:",
            validation[
                "calculated_distances"
            ]
        )

        print(
            "Coordinate validation:",
            validation["valid"]
        )

    # ==================================================
    # COORDINATE GENERATOR ERROR TESTS
    # ==================================================

    print()
    print(
        "========================================"
    )
    print(
        "===== COORDINATE ERROR TEST ====="
    )
    print(
        "========================================"
    )

    try:

        generate_coordinates(
            "linear",
            [1.16]
        )

    except ValueError as error:

        print(
            "Missing bond length test: PASS"
        )

        print(
            "Error:",
            error
        )

    try:

        generate_coordinates(
            "linear",
            [
                1.16,
                1.16
            ],
            [
                0.0,
                0.0
            ]
        )

    except ValueError as error:

        print(
            "Invalid central coordinate test: PASS"
        )

        print(
            "Error:",
            error
        )

    try:

        scale_vector(
            [0.0, 0.0, 0.0],
            1.0
        )

    except ValueError as error:

        print(
            "Zero vector test: PASS"
        )

        print(
            "Error:",
            error
        )

    print()
    print(
        "========================================"
    )
    print(
        "===== 3D GEOMETRY TEST COMPLETE ====="
    )
    print(
        "========================================"
    )

    print()
    print(
        "========================================"
    )
    print(
        "===== MOLECULAR POSITION TEST ====="
    )
    print(
        "========================================"
    )

    molecular_geometry_tests = [

        {
            "name": "CO2",
            "geometry": "linear",
            "bonding_domains": 2,
            "lone_pair_domains": 0,
            "bond_lengths": [
                1.16,
                1.16
            ]
        },

        {
            "name": "CH4",
            "geometry": "tetrahedral",
            "bonding_domains": 4,
            "lone_pair_domains": 0,
            "bond_lengths": [
                1.09,
                1.09,
                1.09,
                1.09
            ]
        },

        {
            "name": "NH3",
            "geometry": "tetrahedral",
            "bonding_domains": 3,
            "lone_pair_domains": 1,
            "bond_lengths": [
                1.01,
                1.01,
                1.01
            ]
        },

        {
            "name": "H2O",
            "geometry": "tetrahedral",
            "bonding_domains": 2,
            "lone_pair_domains": 2,
            "bond_lengths": [
                0.96,
                0.96
            ]
        }
    ]

    for case in molecular_geometry_tests:

        print()
        print(
            case["name"]
        )

        print(
            "--------------------"
        )

        coordinates = (
            generate_molecular_coordinates(
                case["geometry"],
                case["bonding_domains"],
                case["lone_pair_domains"],
                case["bond_lengths"]
            )
        )

        print(
            "Bonding domains:",
            case["bonding_domains"]
        )

        print(
            "Lone-pair domains:",
            case["lone_pair_domains"]
        )

        print(
            "Generated coordinates:"
        )

        for coordinate in coordinates:

            print(
                coordinate
            )

        print(
            "Ligand count:",
            len(coordinates) - 1
        )

        print(
            "Expected ligand count:",
            case["bonding_domains"]
        )

        print(
            "Position validation:",
            len(coordinates) - 1
            == case["bonding_domains"]
        )

    print()
    print(
        "========================================"
    )
    print(
        "===== MOLECULAR ANGLE TEST ====="
    )
    print(
        "========================================"
    )

    molecular_angle_tests = [

        {
            "name": "CO2",
            "geometry": "linear",
            "bonding_domains": 2,
            "angle": 180.0
        },

        {
            "name": "BF3",
            "geometry": "trigonal_planar",
            "bonding_domains": 3,
            "angle": 120.0
        },

        {
            "name": "CH4",
            "geometry": "tetrahedral",
            "bonding_domains": 4,
            "angle": 109.5
        },

        {
            "name": "NH3",
            "geometry": "trigonal_pyramidal",
            "bonding_domains": 3,
            "angle": 107.0
        },

        {
            "name": "H2O",
            "geometry": "bent",
            "bonding_domains": 2,
            "angle": 104.5
        }
    ]

    for case in molecular_angle_tests:

        print()
        print(
            case["name"]
        )

        print(
            "--------------------"
        )

        positions = (
            generate_adjusted_ligand_positions(
                case["geometry"],
                case["bonding_domains"],
                case["angle"]
            )
        )

        print(
            "Molecular geometry:",
            case["geometry"]
        )

        print(
            "Target angle:",
            case["angle"]
        )

        print(
            "Ligand positions:"
        )

        for position in positions:

            print(position)

        print(
            "Ligand count:",
            len(positions)
        )   

        angle_validation = (
            validate_molecular_angles(
                positions,
                case["angle"]
            )
        )

        print(
            "Calculated angles:"
        )

        for result in (
            angle_validation[
                "calculated_angles"
            ]
        ):

            print(result)

        print(
            "Angle validation:",
            angle_validation["valid"]
        )

        if not angle_validation["valid"]:

            print(
                "Invalid angles:"
            )

            for invalid in (
                angle_validation[
                    "invalid_angles"
                ]
            ):

                print(invalid)   