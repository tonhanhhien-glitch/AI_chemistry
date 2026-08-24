from chemistry.molecular_engine import analyze_molecule


def analyze_formula(
    atoms: dict,
    central_atom: str,
    charge: int = 0
):
    """
    Adapter giữa Backend và Molecular Engine.
    """

    result = analyze_molecule(
        atoms,
        central_atom,
        charge
    )

    return result