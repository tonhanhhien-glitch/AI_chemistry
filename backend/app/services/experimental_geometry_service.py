"""Thin compatibility layer over the general geometry-evidence model.

The single-angle ``ExperimentalGeometryRecord`` this module used to define -- one
``angle_pattern``, one ``experimental_angle_deg``, mandatory Cartesian coordinates --
could not describe a species with several inequivalent angles, which is most of the
VSEPR table. The real model now lives in
:mod:`app.schemas.geometry_evidence_schema` and the lookup in
:mod:`app.geometry.providers.nist_cccbdb`.

What remains here is identity matching against the local experimental snapshot, for
callers that only need to ask "is there an experimental record for this species?".
"""

from __future__ import annotations

from typing import Any

from app.geometry.providers.base import GeometryQuery
from app.geometry.providers.nist_cccbdb import snapshot_records
from app.geometry.providers.nist_cccbdb import _identity_matches as _matches
from app.schemas.geometry_evidence_schema import MolecularGeometryEvidence

__all__ = ["experimental_records", "match_experimental_geometry", "MolecularGeometryEvidence"]


def experimental_records() -> tuple[MolecularGeometryEvidence, ...]:
    """The reviewed local snapshot of experimental geometries."""

    return snapshot_records()


def match_experimental_geometry(identity: dict[str, Any]) -> MolecularGeometryEvidence | None:
    """One unambiguous experimental record for this identity, or ``None``.

    Matching prefers strong identifiers (InChIKey, CAS, canonical identity, curated
    id) and falls back to formula plus charge only for records explicitly flagged as
    having an unambiguous formula. Two matches mean the identity is not pinned, so
    nothing is returned rather than guessing.
    """

    query = GeometryQuery(
        formula=str(identity.get("formula", "")),
        charge=int(identity.get("charge", 0)),
        atom_inventory=dict(identity.get("atom_inventory") or {}),
        inchikey=identity.get("inchikey"),
        cas_rn=identity.get("cas_rn"),
        canonical_identity=identity.get("canonical_identity"),
        curated_molecule_id=identity.get("id"),
    )
    matches = [record for record in experimental_records() if _matches(record.identity, query)]
    return matches[0] if len(matches) == 1 else None
