"""Optional deterministic RDKit ETKDG conformer generation from validated SMILES."""

from dataclasses import dataclass
from functools import lru_cache

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
    structure, state, message = _embed_cached(smiles)
    # The status model is mutable, so build a fresh one per call rather than
    # handing every request a shared instance out of the cache.
    return RDKitResult(structure, _status(state, message))


@lru_cache(maxsize=256)
def _embed_cached(smiles: str) -> tuple[RDKitStructure | None, ExternalServiceState, str | None]:
    """Embed and optimize once per SMILES.

    ETKDG plus force-field optimization is the slowest deterministic stage of
    /analyze, and the seed is fixed, so the same SMILES always yields the same
    conformer. Only frozen values are cached.
    """

    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
    except ImportError:
        return None, ExternalServiceState.UNAVAILABLE, "RDKit is not installed."
    try:
        base = Chem.MolFromSmiles(smiles)
        if base is None:
            return None, ExternalServiceState.INVALID_RESPONSE, "Validated SMILES could not be parsed."
        molecule = Chem.AddHs(base)
        parameters = AllChem.ETKDGv3()
        parameters.randomSeed = 0xC0FFEE
        if AllChem.EmbedMolecule(molecule, parameters) != 0:
            return None, ExternalServiceState.CONFORMER_UNAVAILABLE, "ETKDG embedding failed."
        force_field = "none"
        if AllChem.MMFFHasAllMoleculeParams(molecule):
            AllChem.MMFFOptimizeMolecule(molecule, maxIters=250)
            force_field = "MMFF"
        else:
            AllChem.UFFOptimizeMolecule(molecule, maxIters=250)
            force_field = "UFF"
        structure = RDKitStructure(Chem.MolToMolBlock(molecule), force_field=force_field)
        return structure, ExternalServiceState.SUCCESS, None
    except (RuntimeError, ValueError, TypeError):
        return None, ExternalServiceState.CONFORMER_UNAVAILABLE, "Conformer generation failed safely."


def generate_rdkit_molblock(smiles: str | None) -> RDKitStructure | None:
    """Backward-compatible nullable API."""

    return generate_rdkit_result(smiles).structure
