import type { MoleculeDraft, MolecularGeometryEvidenceDraft } from "../../types/moleculeAdmin";

export function emptyMoleculeDraft(): MoleculeDraft {
  return {
    id: "", formula: "", charge: 0, name_vi: "", name_en: "", aliases: [],
    cas_rn: null, pubchem_cid: null, smiles: null, inchi: null, inchikey: null,
    atom_inventory: {}, atom_symbols: [], central_atom: "",
    total_valence_electrons: 0, bond_orders: [], lone_pairs: [], formal_charges: [],
    resonance_forms: 1, resonance_structures: [], resonance_note_vi: null, resonance_note_en: null,
    exception_flags: { electron_deficient: false, expanded_octet: false, odd_electron: false },
    bonding_domains: 0, lone_pair_domains: 0, steric_number: 0, ax_en: "",
    electron_geometry: "", electron_geometry_vi: "", molecular_geometry: "", molecular_geometry_vi: "",
    ideal_angle: "", distortion_note_vi: null, distortion_note_en: null,
    hybridization: null, hybridization_warning_vi: null, hybridization_warning_en: null,
    polarity_note_vi: null, polarity_note_en: null,
    teaching_note_vi: null, teaching_note_en: null,
    misconception_note_vi: null, misconception_note_en: null,
    structure_property_note_vi: null, structure_property_note_en: null,
    three_d_source: { kind: "idealized_vsepr_template", verified_reference: false },
    source: "curated", confidence: "medium", review_status: "draft", review_provenance: null,
  };
}

export function emptyGeometryDraft(formula: string, charge: number): MolecularGeometryEvidenceDraft {
  return {
    id: "", evidence_type: "experimental",
    identity: {
      formula, charge, atom_inventory: {}, inchi: null, inchikey: null, cas_rn: null,
      pubchem_cid: null, canonical_identity: null, curated_molecule_id: null, formula_identity_unambiguous: false,
    },
    atoms: [], bonds: [], bond_lengths: [], bond_angles: [], dihedrals: [], coordinates: null,
    units: "angstrom", phase: null, electronic_state: null, conformation: null, point_group: null,
    source: { name: "", reference: null, url: null, comments: null, retrieved_at: null },
  };
}

let counter = 0;
export function localId(prefix: string): string {
  counter += 1;
  return `${prefix}-${Date.now().toString(36)}-${counter}`;
}
