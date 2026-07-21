# chemistry/periodic_table.py

PERIODIC_TABLE = {

    "H": {
        "name": "Hydrogen",
        "atomic_number": 1,
        "group": 1,
        "period": 1,
        "valence": 1
    },

    "He": {
        "name": "Helium",
        "atomic_number": 2,
        "group": 18,
        "period": 1,
        "valence": 2
    },

    "Li": {
        "name": "Lithium",
        "atomic_number": 3,
        "group": 1,
        "period": 2,
        "valence": 1
    },

    "Be": {
        "name": "Beryllium",
        "atomic_number": 4,
        "group": 2,
        "period": 2,
        "valence": 2
    },

    "B": {
        "name": "Boron",
        "atomic_number": 5,
        "group": 13,
        "period": 2,
        "valence": 3
    },

    "C": {
        "name": "Carbon",
        "atomic_number": 6,
        "group": 14,
        "period": 2,
        "valence": 4
    },

    "N": {
        "name": "Nitrogen",
        "atomic_number": 7,
        "group": 15,
        "period": 2,
        "valence": 5
    },

    "O": {
        "name": "Oxygen",
        "atomic_number": 8,
        "group": 16,
        "period": 2,
        "valence": 6
    },

    "F": {
        "name": "Fluorine",
        "atomic_number": 9,
        "group": 17,
        "period": 2,
        "valence": 7
    },

    "Ne": {
        "name": "Neon",
        "atomic_number": 10,
        "group": 18,
        "period": 2,
        "valence": 8
    },

    "Na": {
        "name": "Sodium",
        "atomic_number": 11,
        "group": 1,
        "period": 3,
        "valence": 1
    },

    "Mg": {
        "name": "Magnesium",
        "atomic_number": 12,
        "group": 2,
        "period": 3,
        "valence": 2
    },

    "Al": {
        "name": "Aluminium",
        "atomic_number": 13,
        "group": 13,
        "period": 3,
        "valence": 3
    },

    "Si": {
        "name": "Silicon",
        "atomic_number": 14,
        "group": 14,
        "period": 3,
        "valence": 4
    },

    "P": {
        "name": "Phosphorus",
        "atomic_number": 15,
        "group": 15,
        "period": 3,
        "valence": 5
    },

    "S": {
        "name": "Sulfur",
        "atomic_number": 16,
        "group": 16,
        "period": 3,
        "valence": 6
    },

    "Cl": {
        "name": "Chlorine",
        "atomic_number": 17,
        "group": 17,
        "period": 3,
        "valence": 7
    },

    "Ar": {
        "name": "Argon",
        "atomic_number": 18,
        "group": 18,
        "period": 3,
        "valence": 8
    },

    "K": {
        "name": "Potassium",
        "atomic_number": 19,
        "group": 1,
        "period": 4,
        "valence": 1
    },

    "Ca": {
        "name": "Calcium",
        "atomic_number": 20,
        "group": 2,
        "period": 4,
        "valence": 2
    },

    "Br": {
        "name": "Bromine",
        "atomic_number": 35,
        "group": 17,
        "period": 4,
        "valence": 7
    },

    "I": {
        "name": "Iodine",
        "atomic_number": 53,
        "group": 17,
        "period": 5,
        "valence": 7
    },

    "Xe": {
        "name": "Xenon",
        "atomic_number": 54,
        "group": 18,
        "period": 5,
        "valence": 8
    }

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

if __name__ == "__main__":

    print("Carbon")
    print(get_element("C"))

    print()

    print("Valence:", get_valence("O"))
    print("Group:", get_group("Cl"))
    print("Period:", get_period("Xe"))