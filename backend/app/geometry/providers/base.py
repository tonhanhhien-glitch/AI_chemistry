"""The geometry-provider contract every geometry source implements.

A provider answers one question -- "what does *my* source say about this species'
geometry?" -- and answers it as typed evidence plus a typed status. It never
raises for an outage: a provider that cannot answer returns ``evidence=None`` with
a status explaining why, so a NIST or PubChem failure degrades the geometry layer
without touching local Lewis/VSEPR analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from app.schemas.geometry_evidence_schema import MolecularGeometryEvidence
from app.schemas.molecule_schema import ExternalServiceState, ExternalServiceStatus


@dataclass(frozen=True, slots=True)
class GeometryQuery:
    """Everything a provider may match on, strongest identifier first."""

    formula: str
    charge: int
    atom_inventory: dict[str, int]
    central_atom: str | None = None
    inchikey: str | None = None
    inchi: str | None = None
    cas_rn: str | None = None
    pubchem_cid: int | None = None
    canonical_identity: str | None = None
    curated_molecule_id: str | None = None
    smiles: str | None = None
    record: dict[str, Any] | None = None
    timeout: float | None = None

    def with_timeout(self, timeout: float) -> "GeometryQuery":
        return GeometryQuery(
            formula=self.formula,
            charge=self.charge,
            atom_inventory=self.atom_inventory,
            central_atom=self.central_atom,
            inchikey=self.inchikey,
            inchi=self.inchi,
            cas_rn=self.cas_rn,
            pubchem_cid=self.pubchem_cid,
            canonical_identity=self.canonical_identity,
            curated_molecule_id=self.curated_molecule_id,
            smiles=self.smiles,
            record=self.record,
            timeout=timeout,
        )

    @classmethod
    def from_record(cls, record: dict[str, Any]) -> "GeometryQuery":
        return cls(
            formula=str(record.get("formula", "")),
            charge=int(record.get("charge", 0)),
            atom_inventory=dict(record.get("atom_inventory") or {}),
            central_atom=record.get("central_atom"),
            inchikey=record.get("inchikey"),
            inchi=record.get("inchi"),
            cas_rn=record.get("cas_rn"),
            pubchem_cid=record.get("pubchem_cid"),
            canonical_identity=record.get("canonical_identity"),
            curated_molecule_id=record.get("id"),
            smiles=record.get("smiles"),
            record=record,
        )


@dataclass(frozen=True, slots=True)
class GeometryProviderResult:
    evidence: MolecularGeometryEvidence | None
    status: ExternalServiceStatus

    @property
    def found(self) -> bool:
        return self.evidence is not None


class GeometryEvidenceProvider(Protocol):
    """Structural type for a geometry source."""

    name: str
    service: str

    def fetch(self, query: GeometryQuery) -> GeometryProviderResult:
        """Return this source's geometry evidence, or a typed miss."""
        ...


def provider_status(
    service: str,
    state: ExternalServiceState,
    *,
    cache_hit: bool = False,
    message: str | None = None,
) -> ExternalServiceStatus:
    return ExternalServiceStatus(service=service, state=state, cache_hit=cache_hit, message=message)
