"""Optional deterministic RDKit ETKDG conformer generation from validated SMILES."""

from dataclasses import dataclass

from app.core.config import settings
from app.schemas.molecule_schema import ExternalServiceState, ExternalServiceStatus


@dataclass(frozen=True, slots=True)
class RDKitStructure:
    molblock: str
    source: str = "RDKit ETKDGv3"
    is_illustrative: bool = False
    is_computed: bool = True
    force_field: str = "none"


@dataclass(frozen=True, slots=True)
class RDKitResult:
    structure: RDKitStructure | None
    status: ExternalServiceStatus


def _status(state: ExternalServiceState, message: str | None = None) -> ExternalServiceStatus:
    return ExternalServiceStatus(service="RDKit", state=state, message=message)


def generate_rdkit_result(smiles: str | None) -> RDKitResult:
    if not settings.ENABLE_RDKIT:
        return RDKitResult(None, _status(ExternalServiceState.DISABLED))
    if not smiles:
        return RDKitResult(None, _status(ExternalServiceState.CONFORMER_UNAVAILABLE, "No validated SMILES was available."))
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
    except ImportError:
        return RDKitResult(None, _status(ExternalServiceState.UNAVAILABLE, "RDKit is not installed."))
    try:
        base = Chem.MolFromSmiles(smiles)
        if base is None:
            return RDKitResult(None, _status(ExternalServiceState.INVALID_RESPONSE, "Validated SMILES could not be parsed."))
        molecule = Chem.AddHs(base)
        parameters = AllChem.ETKDGv3()
        parameters.randomSeed = 0xC0FFEE
        if AllChem.EmbedMolecule(molecule, parameters) != 0:
            return RDKitResult(None, _status(ExternalServiceState.CONFORMER_UNAVAILABLE, "ETKDG embedding failed."))
        force_field = "none"
        if AllChem.MMFFHasAllMoleculeParams(molecule):
            AllChem.MMFFOptimizeMolecule(molecule, maxIters=250)
            force_field = "MMFF"
        else:
            AllChem.UFFOptimizeMolecule(molecule, maxIters=250)
            force_field = "UFF"
        return RDKitResult(
            RDKitStructure(Chem.MolToMolBlock(molecule), force_field=force_field),
            _status(ExternalServiceState.SUCCESS),
        )
    except (RuntimeError, ValueError, TypeError):
        return RDKitResult(None, _status(ExternalServiceState.CONFORMER_UNAVAILABLE, "Conformer generation failed safely."))


def generate_rdkit_molblock(smiles: str | None) -> RDKitStructure | None:
    """Backward-compatible nullable API."""

    return generate_rdkit_result(smiles).structure
