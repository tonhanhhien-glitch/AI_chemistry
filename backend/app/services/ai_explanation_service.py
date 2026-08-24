"""Calls the Anthropic Claude API to turn verified backend facts into a leveled explanation, without letting the model alter chemistry conclusions."""
def build_explanation_payload(result: dict):
    """
    Chuẩn hóa dữ liệu từ Molecular Engine trước khi gửi cho AI.
    """

    return {
        "formula": result.get("formula"),
        "geometry": result["vsepr"]["molecular_geometry"],
        "bond_angle": result["vsepr"]["characteristic_bond_angle"],
        "electron_geometry": result["vsepr"]["electron_geometry"],
        "resonance": result.get("resonance"),
        "formal_charge": result["lewis"]["total_formal_charge"],
    }