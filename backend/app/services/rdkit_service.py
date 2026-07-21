"""Optional RDKit conformer generation from validated SMILES only."""

from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True, slots=True)
class RDKitStructure:
    molblock: str
    source: str = "RDKit ETKDG"
    is_illustrative: bool = False


def generate_rdkit_molblock(smiles: str | None) -> RDKitStructure | None:
    if not (settings.ENABLE_RDKIT and smiles):
        return None
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem

        molecule = Chem.AddHs(Chem.MolFromSmiles(smiles))
        if molecule is None:
            return None
        parameters = AllChem.ETKDGv3(); parameters.randomSeed = 0xC0FFEE
        if AllChem.EmbedMolecule(molecule, parameters) != 0:
            return None
        try:
            AllChem.MMFFOptimizeMolecule(molecule, maxIters=250)
        except Exception:
            pass
        return RDKitStructure(Chem.MolToMolBlock(molecule))
    except (ImportError, RuntimeError, ValueError):
        return None
