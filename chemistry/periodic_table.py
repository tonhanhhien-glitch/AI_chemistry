# chemistry/periodic_table.py

PERIODIC_TABLE = {

    "H": {
        "name": "Hydrogen",
        "atomic_number": 1,
        "group": 1,
        "period": 1,
        "valence": 1,
        "electronegativity": 2.20,
        "is_metal": False,
        "can_be_central": False,
        "expanded_octet": False,
        "max_octet": 2
    },

    "He": {
        "name": "Helium",
        "atomic_number": 2,
        "group": 18,
        "period": 1,
        "valence": 2,
        "electronegativity": None,
        "is_metal": False,
        "can_be_central": False,
        "expanded_octet": False,
        "max_octet": 2
    },

    "Li": {
        "name": "Lithium",
        "atomic_number": 3,
        "group": 1,
        "period": 2,
        "valence": 1,
        "electronegativity": 0.98,
        "is_metal": True,
        "can_be_central": False,
        "expanded_octet": False,
        "max_octet": 2
    },

    "Be": {
        "name": "Beryllium",
        "atomic_number": 4,
        "group": 2,
        "period": 2,
        "valence": 2,
        "electronegativity": 1.57,
        "is_metal": True,
        "can_be_central": True,
        "expanded_octet": False,
        "max_octet": 4
    },

    "B": {
        "name": "Boron",
        "atomic_number": 5,
        "group": 13,
        "period": 2,
        "valence": 3,
        "electronegativity": 2.04,
        "is_metal": False,
        "can_be_central": True,
        "expanded_octet": False,
        "max_octet": 6
    },

    "C": {
        "name": "Carbon",
        "atomic_number": 6,
        "group": 14,
        "period": 2,
        "valence": 4,
        "electronegativity": 2.55,
        "is_metal": False,
        "can_be_central": True,
        "expanded_octet": False,
        "max_octet": 8
    },

    "N": {
        "name": "Nitrogen",
        "atomic_number": 7,
        "group": 15,
        "period": 2,
        "valence": 5,
        "electronegativity": 3.04,
        "is_metal": False,
        "can_be_central": True,
        "expanded_octet": False,
        "max_octet": 8
    },

    "O": {
        "name": "Oxygen",
        "atomic_number": 8,
        "group": 16,
        "period": 2,
        "valence": 6,
        "electronegativity": 3.44,
        "is_metal": False,
        "can_be_central": True,
        "expanded_octet": False,
        "max_octet": 8
    },

    "F": {
        "name": "Fluorine",
        "atomic_number": 9,
        "group": 17,
        "period": 2,
        "valence": 7,
        "electronegativity": 3.98,
        "is_metal": False,
        "can_be_central": False,
        "expanded_octet": False,
        "max_octet": 8
    },

    "Ne": {
        "name": "Neon",
        "atomic_number": 10,
        "group": 18,
        "period": 2,
        "valence": 8,
        "electronegativity": None,
        "is_metal": False,
        "can_be_central": False,
        "expanded_octet": False,
        "max_octet": 8
    },

    "Na": {
        "name": "Sodium",
        "atomic_number": 11,
        "group": 1,
        "period": 3,
        "valence": 1,
        "electronegativity": 0.93,
        "is_metal": True,
        "can_be_central": False,
        "expanded_octet": False,
        "max_octet": 8
    },

    "Mg": {
        "name": "Magnesium",
        "atomic_number": 12,
        "group": 2,
        "period": 3,
        "valence": 2,
        "electronegativity": 1.31,
        "is_metal": True,
        "can_be_central": True,
        "expanded_octet": False,
        "max_octet": 8
    },

    "Al": {
        "name": "Aluminium",
        "atomic_number": 13,
        "group": 13,
        "period": 3,
        "valence": 3,
        "electronegativity": 1.61,
        "is_metal": True,
        "can_be_central": True,
        "expanded_octet": True,
        "max_octet": 6
    },

    "Si": {
        "name": "Silicon",
        "atomic_number": 14,
        "group": 14,
        "period": 3,
        "valence": 4,
        "electronegativity": 1.90,
        "is_metal": False,
        "can_be_central": True,
        "expanded_octet": True,
        "max_octet": 12
    },

    "P": {
        "name": "Phosphorus",
        "atomic_number": 15,
        "group": 15,
        "period": 3,
        "valence": 5,
        "electronegativity": 2.19,
        "is_metal": False,
        "can_be_central": True,
        "expanded_octet": True,
        "max_octet": 10
    },

    "S": {
        "name": "Sulfur",
        "atomic_number": 16,
        "group": 16,
        "period": 3,
        "valence": 6,
        "electronegativity": 2.58,
        "is_metal": False,
        "can_be_central": True,
        "expanded_octet": True,
        "max_octet": 12
    },

    "Cl": {
        "name": "Chlorine",
        "atomic_number": 17,
        "group": 17,
        "period": 3,
        "valence": 7,
        "electronegativity": 3.16,
        "is_metal": False,
        "can_be_central": True,
        "expanded_octet": True,
        "max_octet": 14
    },

    "Ar": {
        "name": "Argon",
        "atomic_number": 18,
        "group": 18,
        "period": 3,
        "valence": 8,
        "electronegativity": None,
        "is_metal": False,
        "can_be_central": False,
        "expanded_octet": False,
        "max_octet": 8
    },

    "K": {
        "name": "Potassium",
        "atomic_number": 19,
        "group": 1,
        "period": 4,
        "valence": 1,
        "electronegativity": 0.82,
        "is_metal": True,
        "can_be_central": False,
        "expanded_octet": False,
        "max_octet": 8
    },

    "Ca": {
        "name": "Calcium",
        "atomic_number": 20,
        "group": 2,
        "period": 4,
        "valence": 2,
        "electronegativity": 1.00,
        "is_metal": True,
        "can_be_central": False,
        "expanded_octet": False,
        "max_octet": 8
    },

    "Br": {
        "name": "Bromine",
        "atomic_number": 35,
        "group": 17,
        "period": 4,
        "valence": 7,
        "electronegativity": 2.96,
        "is_metal": False,
        "can_be_central": True,
        "expanded_octet": True,
        "max_octet": 14
    },

    "I": {
        "name": "Iodine",
        "atomic_number": 53,
        "group": 17,
        "period": 5,
        "valence": 7,
        "electronegativity": 2.66,
        "is_metal": False,
        "can_be_central": True,
        "expanded_octet": True,
        "max_octet": 14
    },

    "Xe": {
        "name": "Xenon",
        "atomic_number": 54,
        "group": 18,
        "period": 5,
        "valence": 8,
        "electronegativity": 2.60,
        "is_metal": False,
        "can_be_central": True,
        "expanded_octet": True,
        "max_octet": 16
    },

}

def get_element(symbol: str):

    return PERIODIC_TABLE.get(symbol)

def get_valence(symbol: str):

    element = get_element(symbol)

    if element is None:
        return None

    return element["valence"]

def get_group(symbol: str):

    element = get_element(symbol)

    if element is None:
        return None

    return element["group"]


def get_period(symbol: str):

    element = get_element(symbol)

    if element is None:
        return None

    return element["period"]

def get_electronegativity(symbol: str):

    element = get_element(symbol)

    if element is None:
        return None

    return element["electronegativity"]

if __name__ == "__main__":

    print("Carbon")
    print(get_element("C"))

    print()

    print("Valence:", get_valence("O"))
    print("Group:", get_group("Cl"))
    print("Period:", get_period("Xe"))
    print("Electronegativity:", get_electronegativity("F"))