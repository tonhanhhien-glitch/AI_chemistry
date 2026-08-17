"""Computed-conformer geometry providers: PubChem 3D and RDKit ETKDG.

Both emit :attr:`GeometryEvidenceType.COMPUTED_CONFORMER`. Neither is ever
labelled experimental, no matter how good the conformer is.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.geometry.providers.base import GeometryProviderResult, GeometryQuery, provider_status
from app.schemas.geometry_evidence_schema import (
    BondAngleObservation,
    BondLengthObservation,
    GeometryAtom,
    GeometryBond,
    GeometryCoordinate,
    GeometryEvidenceType,
    GeometryIdentity,
    GeometrySource,
    MolecularGeometryEvidence,
)
from app.schemas.molecule_schema import ExternalServiceState
from app.services.connectivity_service import MolecularGraph, parse_molfile
from app.services.pubchem_service import fetch_pubchem_3d
from app.services.rdkit_service import generate_rdkit_result


def _identity(query: GeometryQuery) -> GeometryIdentity:
    return GeometryIdentity(
        formula=query.formula, charge=query.charge, atom_inventory=dict(query.atom_inventory),
        inchi=query.inchi, inchikey=query.inchikey, cas_rn=query.cas_rn,
        pubchem_cid=query.pubchem_cid, canonical_identity=query.canonical_identity,
        curated_molecule_id=query.curated_molecule_id,
    )


def evidence_from_graph(
    graph: MolecularGraph,
    query: GeometryQuery,
    *,
    record_id: str,
    source: GeometrySource,
    evidence_type: GeometryEvidenceType = GeometryEvidenceType.COMPUTED_CONFORMER,
) -> MolecularGeometryEvidence | None:
    """Turn a coordinate-carrying molecular graph into geometry evidence.

    The graph must match the requested atom inventory and be a single-centre star,
    which is the topology this application's VSEPR scope covers.
    """

    if not graph.has_coordinates or graph.coordinate_dimension != 3:
        return None
    if query.atom_inventory and dict(graph.inventory()) != query.atom_inventory:
        return None
    if graph.fragment_count != 1:
        return None
    center_id = graph.single_center_id(query.central_atom)
    if center_id is None:
        return None

    ordered = [next(atom for atom in graph.atoms if atom.id == center_id)]
    ordered.extend(atom for atom in graph.atoms if atom.id != center_id)
    positions = {atom.id: (float(atom.x or 0.0), float(atom.y or 0.0), float(atom.z or 0.0)) for atom in ordered}

    from app.geometry.fitter import angle_degrees, distance

    lengths = []
    for index, atom in enumerate(ordered[1:]):
        lengths.append(BondLengthObservation(
            id=f"len-{index}", atom1_id=center_id, atom2_id=atom.id,
            value_angstrom=distance(positions[center_id], positions[atom.id]),
            label=f"{ordered[0].element}–{atom.element}",
        ))
    angles = []
    ligands = ordered[1:]
    counter = 0
    for first in range(len(ligands)):
        for second in range(first + 1, len(ligands)):
            angles.append(BondAngleObservation(
                id=f"ang-{counter}", atom1_id=ligands[first].id, center_atom_id=center_id,
                atom2_id=ligands[second].id,
                value_deg=angle_degrees(positions[ligands[first].id], positions[center_id], positions[ligands[second].id]),
                label=f"{ligands[first].element}–{ordered[0].element}–{ligands[second].element}",
            ))
            counter += 1

    return MolecularGeometryEvidence(
        id=record_id,
        identity=_identity(query),
        evidence_type=evidence_type,
        atoms=[
            GeometryAtom(id=atom.id, element=atom.element, role="center" if atom.id == center_id else "ligand")
            for atom in ordered
        ],
        bonds=[
            GeometryBond(
                atom1_id=center_id, atom2_id=atom.id,
                order=graph.bond_order(center_id, atom.id) or 1,
            )
            for atom in ligands
        ],
        bond_lengths=lengths,
        bond_angles=angles,
        coordinates=[
            GeometryCoordinate(
                id=atom.id, element=atom.element,
                x=positions[atom.id][0], y=positions[atom.id][1], z=positions[atom.id][2],
            )
            for atom in ordered
        ],
        phase=None,
        source=source,
    )


class PubChemGeometryProvider:
    """PubChem's precomputed 3D conformer. Computed, not measured."""

    name = "pubchem_3d"
    service = "PubChem"

    def fetch(self, query: GeometryQuery) -> GeometryProviderResult:
        if query.pubchem_cid is None:
            return GeometryProviderResult(None, provider_status(
                self.service, ExternalServiceState.NOT_FOUND,
                message="No PubChem CID was resolved for this identity.",
            ))
        result = fetch_pubchem_3d(int(query.pubchem_cid))
        if not result.data:
            return GeometryProviderResult(None, result.status)
        graph = parse_molfile(result.data)
        if graph is None:
            return GeometryProviderResult(None, provider_status(self.service, ExternalServiceState.INVALID_RESPONSE))
        evidence = evidence_from_graph(
            graph, query,
            record_id=f"pubchem-3d-{query.pubchem_cid}",
            source=GeometrySource(
                name="PubChem",
                reference=f"PubChem CID {query.pubchem_cid} 3D conformer",
                url=f"https://pubchem.ncbi.nlm.nih.gov/compound/{query.pubchem_cid}#section=3D-Conformer",
                comments="Computed 3D conformer published by PubChem. This is a calculation, not a measurement.",
                retrieved_at=datetime.now(UTC),
            ),
        )
        if evidence is None:
            return GeometryProviderResult(None, provider_status(
                self.service, ExternalServiceState.UNSUPPORTED_CHEMISTRY,
                message="The PubChem conformer is not a single-centre structure in scope.",
            ))
        return GeometryProviderResult(evidence, result.status)


class RdkitGeometryProvider:
    """A locally generated RDKit ETKDGv3 conformer. Computed, not measured."""

    name = "rdkit_etkdg"
    service = "RDKit"

    def fetch(self, query: GeometryQuery) -> GeometryProviderResult:
        result = generate_rdkit_result(query.smiles)
        if result.structure is None:
            return GeometryProviderResult(None, result.status)
        graph = parse_molfile(result.structure.molblock)
        if graph is None:
            return GeometryProviderResult(None, provider_status(self.service, ExternalServiceState.INVALID_RESPONSE))
        evidence = evidence_from_graph(
            graph, query,
            record_id=f"rdkit-{query.formula.casefold()}",
            source=GeometrySource(
                name="RDKit",
                reference=f"ETKDGv3 embedding, {result.structure.force_field} optimisation",
                comments="Conformer generated locally by RDKit. This is a calculation, not a measurement.",
                retrieved_at=datetime.now(UTC),
            ),
        )
        if evidence is None:
            return GeometryProviderResult(None, provider_status(
                self.service, ExternalServiceState.UNSUPPORTED_CHEMISTRY,
                message="The RDKit conformer is not a single-centre structure in scope.",
            ))
        return GeometryProviderResult(evidence, result.status)
