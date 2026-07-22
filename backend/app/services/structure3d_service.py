"""Return an idealized VSEPR coordinate schema with explicit limitations."""

from functools import lru_cache
from pathlib import Path
from typing import Any

from app.schemas.structure3d_schema import Structure3D, Structure3DAtom, Structure3DBond
from app.utils.file_loader import load_json

_DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "geometry_templates_3d.json"


@lru_cache(maxsize=1)
def _templates() -> dict[str, Any]:
    return load_json(_DATA_FILE)["geometries"]


def get_structure3d(record: dict[str, Any]) -> Structure3D:
    template = _templates()[record["ax_en"]]
    coordinates = [[0.0, 0.0, 0.0], *template["ligands"]]
    scale = 1.55
    atoms = [Structure3DAtom(id=f"a{i}", element=symbol, x=round(coordinates[i][0] * scale, 4), y=round(coordinates[i][1] * scale, 4), z=round(coordinates[i][2] * scale, 4)) for i, symbol in enumerate(record["atom_symbols"])]
    bonds = [Structure3DBond(atom1_id="a0", atom2_id=f"a{i + 1}", order=order) for i, order in enumerate(record["bond_orders"])]
    return Structure3D(
        atoms=atoms, bonds=bonds, source="curated_vsepr_template", is_illustrative=True,
        warning_vi="This 3D model is an idealized VSEPR geometry for illustration, not a quantum-optimized structure or experimental data.",
    )
