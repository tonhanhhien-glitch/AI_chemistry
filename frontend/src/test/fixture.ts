import type { AnalysisResult } from "../types/analysis";

// Generated from the live backend contract via backend/scripts/export_frontend_fixtures.py.
// Regenerate after any schema change so the frontend tests cannot drift from the API.

export const waterAnalysis: AnalysisResult = {
  "schema_version": "1.1",
  "molecule": {
    "id": "h2o",
    "formula": "H2O",
    "name_vi": "Water",
    "name_en": "Water",
    "ax_en": "AX2E2",
    "molecular_geometry": "bent",
    "molecular_geometry_vi": "gấp khúc",
    "review_status": "internal_golden_pending_expert_signoff",
    "charge": 0,
    "atom_inventory": {
      "H": 2,
      "O": 1
    },
    "central_atom": "O",
    "source": "curated",
    "confidence": "high",
    "pubchem_cid": null,
    "smiles": "O",
    "canonical_identity": null,
    "inchi": null,
    "inchikey": null,
    "validation_status": "curated_verified",
    "cache_timestamp": null,
    "connectivity": {
      "atoms": [
        {
          "id": "a0",
          "element": "O"
        },
        {
          "id": "a1",
          "element": "H"
        },
        {
          "id": "a2",
          "element": "H"
        }
      ],
      "bonds": [
        {
          "atom1_id": "a0",
          "atom2_id": "a1",
          "order": 1
        },
        {
          "atom1_id": "a0",
          "atom2_id": "a2",
          "order": 1
        }
      ],
      "central_atom_id": "a0"
    }
  },
  "lewis": {
    "atoms": [
      {
        "id": "a0",
        "element": "O",
        "x": 160.0,
        "y": 113.8586,
        "lone_pairs": 2,
        "formal_charge": 0
      },
      {
        "id": "a1",
        "element": "H",
        "x": 76.9776,
        "y": 178.1414,
        "lone_pairs": 0,
        "formal_charge": 0
      },
      {
        "id": "a2",
        "element": "H",
        "x": 243.0224,
        "y": 178.1414,
        "lone_pairs": 0,
        "formal_charge": 0
      }
    ],
    "bonds": [
      {
        "id": "b0",
        "atom1_id": "a0",
        "atom2_id": "a1",
        "order": 1
      },
      {
        "id": "b1",
        "atom1_id": "a0",
        "atom2_id": "a2",
        "order": 1
      }
    ],
    "central_atom_id": "a0",
    "total_valence_electrons": 8,
    "resonance_forms": 1,
    "resonance_note_vi": null,
    "resonance_note_en": null,
    "resonance_structures": [],
    "exception_flags": {
      "electron_deficient": false,
      "expanded_octet": false,
      "odd_electron": false,
      "note_vi": null
    },
    "source": "curated",
    "confidence": "high",
    "review_status": "internal_golden_pending_expert_signoff"
  },
  "vsepr": {
    "bonding_domains": 2,
    "lone_pair_domains": 2,
    "steric_number": 4,
    "ax_en": "AX2E2",
    "electron_geometry": "tetrahedral",
    "electron_geometry_vi": "tetrahedral",
    "molecular_geometry": "bent",
    "molecular_geometry_vi": "bent",
    "ideal_angle": "<109.5°",
    "reference_angles": [
      {
        "display_label": "~104.5°",
        "source": "VSEPR teaching reference",
        "is_approximate": true,
        "note_vi": "Hai cặp electron tự do nén góc H–O–H từ góc tứ diện lý tưởng.",
        "note_en": "Two lone pairs compress the H-O-H angle from the ideal tetrahedral angle."
      }
    ],
    "distortion_note_vi": "Hai cặp electron tự do nén góc H–O–H từ góc tứ diện lý tưởng.",
    "distortion_note_en": "Two lone pairs compress the H-O-H angle from the ideal tetrahedral angle.",
    "teaching_note_vi": "Cặp electron tự do đẩy mạnh hơn cặp electron liên kết.",
    "teaching_note_en": "A lone pair repels more strongly than a bonding pair.",
    "pedagogical_hybridization": "sp³",
    "hybridization_warning_vi": "Nhãn lai hoá là mô hình sư phạm gần đúng theo VSEPR, không phải mô tả liên kết hiện đại đầy đủ.",
    "hybridization_warning_en": "The hybridization label is an approximate VSEPR-style pedagogical model, not a full modern description of bonding."
  },
  "properties": [
    {
      "key": "molar_mass",
      "category": "physical",
      "label_vi": "Khối lượng mol",
      "label_en": "Molar mass",
      "value": 18.015,
      "unit": "g/mol",
      "uncertainty": null,
      "conditions": null,
      "phase": null,
      "evidence_type": "computed",
      "source_name": "Standard atomic weights (IUPAC)",
      "source_name_en": "Standard atomic weights (IUPAC)",
      "source_name_vi": "Khối lượng nguyên tử chuẩn (IUPAC)",
      "source_reference": null,
      "source_url": null,
      "applicability": "applicable",
      "retrieved_at": null,
      "notes_vi": null,
      "notes_en": null,
      "observations": []
    },
    {
      "key": "central_atom_electronegativity",
      "category": "structural",
      "label_vi": "Độ âm điện nguyên tử trung tâm",
      "label_en": "Central-atom electronegativity",
      "value": 3.44,
      "unit": "Pauling",
      "uncertainty": null,
      "conditions": null,
      "phase": null,
      "evidence_type": "deterministic",
      "source_name": "Deterministic chemistry engine",
      "source_reference": null,
      "source_url": null,
      "applicability": "applicable",
      "retrieved_at": null,
      "notes_vi": null,
      "notes_en": null,
      "observations": []
    },
    {
      "key": "polarity",
      "category": "chemical",
      "label_vi": "Nhận xét về độ phân cực",
      "label_en": "Polarity note",
      "value": "The molecule is polar because of its bent shape.",
      "value_vi": "Phân tử phân cực do hình gấp khúc.",
      "value_en": "The molecule is polar because of its bent shape.",
      "unit": null,
      "uncertainty": null,
      "conditions": null,
      "phase": null,
      "evidence_type": "curated",
      "source_name": "Curated teaching record",
      "source_reference": null,
      "source_url": null,
      "applicability": "applicable",
      "retrieved_at": null,
      "notes_vi": null,
      "notes_en": null,
      "observations": []
    }
  ],
  "structure3d": {
    "format": "coordinates",
    "atoms": [
      {
        "id": "a0",
        "element": "O",
        "x": 0.0,
        "y": 0.0,
        "z": 0.0
      },
      {
        "id": "a1",
        "element": "H",
        "x": 0.8666080370820473,
        "y": 0.8666080370820473,
        "z": 0.9489367840533963
      },
      {
        "id": "a2",
        "element": "H",
        "x": -0.8666080370820473,
        "y": -0.8666080370820473,
        "z": 0.9489367840533963
      }
    ],
    "bonds": [
      {
        "atom1_id": "a0",
        "atom2_id": "a1",
        "order": 1
      },
      {
        "atom1_id": "a0",
        "atom2_id": "a2",
        "order": 1
      }
    ],
    "data": null,
    "source": "idealized_vsepr",
    "source_label": "Idealized VSEPR model at the 104.5° reference angle",
    "evidence_type": "ideal_vsepr",
    "geometry_evidence": {
      "id": "ideal-vsepr-ax2e2-h2o",
      "evidence_type": "ideal_vsepr",
      "provider": "ideal_vsepr",
      "source_name": "Idealized VSEPR model",
      "source_reference": "AX2E2",
      "source_url": null,
      "source_comments": "Educational idealization built from the AXnEm electron-domain table. Bond lengths are uniform and illustrative, not measured. Ligand directions were opened to the molecule-specific reference angle 104.50° (Curated molecule-specific teaching reference).",
      "retrieved_at": null,
      "phase": null,
      "electronic_state": null,
      "conformation": null,
      "point_group": null,
      "units": "angstrom",
      "bond_lengths": [
        {
          "label": "O–H",
          "value_angstrom": 1.55,
          "uncertainty_angstrom": null,
          "equivalent_count": 2
        }
      ],
      "bond_length_count": 2,
      "bond_angle_count": 1,
      "dihedral_count": 0,
      "coordinates_are_fitted": false,
      "max_length_deviation_angstrom": 0.0,
      "max_angle_deviation_deg": 0.0,
      "is_experimental": false,
      "is_computed": false,
      "is_ideal": true,
      "provenance_label_vi": "Minh họa VSEPR lý tưởng hóa",
      "provenance_label_en": "Idealized VSEPR illustration"
    },
    "is_illustrative": true,
    "is_computed": false,
    "is_experimental": false,
    "pubchem_cid": null,
    "central_atom_id": "a0",
    "reference_bond_angle": {
      "value_deg": 104.5,
      "display_label": "~104.5°",
      "category": "curated_reference",
      "source": "Curated molecule-specific teaching reference",
      "is_approximate": true,
      "deprecated": true
    },
    "angle_annotations": [
      {
        "id": "angle-0",
        "atom1_id": "a1",
        "center_atom_id": "a0",
        "atom2_id": "a2",
        "value_deg": 104.50000000000001,
        "coordinate_value_deg": 104.50000000000001,
        "source_value_deg": null,
        "deviation_deg": null,
        "uncertainty_deg": null,
        "display_label": "104.5°",
        "category": "ideal_vsepr",
        "evidence_type": "ideal_vsepr",
        "source": "Idealized VSEPR model at the 104.5° reference angle",
        "source_reference": "AX2E2",
        "source_url": null,
        "phase": null,
        "is_approximate": true,
        "equivalent_count": 1,
        "note_vi": "Góc được tính trực tiếp từ tọa độ đang hiển thị.",
        "note_en": "Angle calculated directly from the rendered coordinates."
      }
    ],
    "electron_domains": [
      {
        "id": "bond-domain-0",
        "center_atom_id": "a0",
        "kind": "bonding",
        "occupancy": 2,
        "direction": {
          "x": 0.5591019594077724,
          "y": 0.5591019594077724,
          "z": 0.6122172800344492
        },
        "position": {
          "x": 0.43330401854102363,
          "y": 0.43330401854102363,
          "z": 0.47446839202669816
        },
        "source": "Idealized VSEPR model at the 104.5° reference angle",
        "is_illustrative": true,
        "label_vi": "Miền electron liên kết",
        "label_en": "Bonding electron domain"
      },
      {
        "id": "bond-domain-1",
        "center_atom_id": "a0",
        "kind": "bonding",
        "occupancy": 2,
        "direction": {
          "x": -0.5591019594077724,
          "y": -0.5591019594077724,
          "z": 0.6122172800344492
        },
        "position": {
          "x": -0.43330401854102363,
          "y": -0.43330401854102363,
          "z": 0.47446839202669816
        },
        "source": "Idealized VSEPR model at the 104.5° reference angle",
        "is_illustrative": true,
        "label_vi": "Miền electron liên kết",
        "label_en": "Bonding electron domain"
      },
      {
        "id": "lone-pair-0",
        "center_atom_id": "a0",
        "kind": "lone_pair",
        "occupancy": 2,
        "direction": {
          "x": -0.5773502691896257,
          "y": 0.5773502691896257,
          "z": -0.5773502691896257
        },
        "position": {
          "x": -0.6639528095680696,
          "y": 0.6639528095680696,
          "z": -0.6639528095680696
        },
        "source": "illustrative VSEPR orientation",
        "is_illustrative": true,
        "label_vi": "Miền cặp electron tự do (minh họa)",
        "label_en": "Lone-pair electron domain (illustrative)"
      },
      {
        "id": "lone-pair-1",
        "center_atom_id": "a0",
        "kind": "lone_pair",
        "occupancy": 2,
        "direction": {
          "x": 0.5773502691896257,
          "y": -0.5773502691896257,
          "z": -0.5773502691896257
        },
        "position": {
          "x": 0.6639528095680696,
          "y": -0.6639528095680696,
          "z": -0.6639528095680696
        },
        "source": "illustrative VSEPR orientation",
        "is_illustrative": true,
        "label_vi": "Miền cặp electron tự do (minh họa)",
        "label_en": "Lone-pair electron domain (illustrative)"
      }
    ],
    "warning_vi": "Mô hình 3D VSEPR lý tưởng hóa chỉ dùng để minh họa, không phải số liệu đo; góc hiển thị được đo từ chính tọa độ này.",
    "warning_en": "This idealized VSEPR model is an educational illustration, not measured data; displayed angles are measured from these coordinates."
  },
  "bond_angles": {
    "preferred": [
      {
        "id": "curated-h2o",
        "atom1_element": "H",
        "center_element": "O",
        "atom2_element": "H",
        "atom1_id": null,
        "center_atom_id": null,
        "atom2_id": null,
        "value_deg": 104.5,
        "coordinate_value_deg": null,
        "display_label": "~104.5°",
        "evidence_type": "curated_reference",
        "source_name": "Curated molecule-specific teaching reference",
        "source_url": null,
        "reference": null,
        "phase": null,
        "uncertainty_deg": null,
        "is_experimental": false,
        "is_computed": false,
        "is_approximate": true,
        "equivalent_count": 1,
        "provenance_label_vi": "Chú giải từ nguồn dữ liệu",
        "provenance_label_en": "Source-derived annotation"
      }
    ],
    "experimental": [],
    "coordinate_derived": [
      {
        "id": "coordinate-angle-0",
        "atom1_element": "H",
        "center_element": "O",
        "atom2_element": "H",
        "atom1_id": "a1",
        "center_atom_id": "a0",
        "atom2_id": "a2",
        "value_deg": 104.50000000000001,
        "coordinate_value_deg": 104.50000000000001,
        "display_label": "104.5°",
        "evidence_type": "ideal_vsepr",
        "source_name": "Idealized VSEPR model",
        "source_url": null,
        "reference": "AX2E2",
        "phase": null,
        "uncertainty_deg": null,
        "is_experimental": false,
        "is_computed": false,
        "is_approximate": true,
        "equivalent_count": 1,
        "provenance_label_vi": "Minh họa VSEPR lý tưởng hóa",
        "provenance_label_en": "Idealized VSEPR illustration"
      }
    ],
    "curated_reference": [
      {
        "id": "curated-h2o",
        "atom1_element": "H",
        "center_element": "O",
        "atom2_element": "H",
        "atom1_id": null,
        "center_atom_id": null,
        "atom2_id": null,
        "value_deg": 104.5,
        "coordinate_value_deg": null,
        "display_label": "~104.5°",
        "evidence_type": "curated_reference",
        "source_name": "Curated molecule-specific teaching reference",
        "source_url": null,
        "reference": null,
        "phase": null,
        "uncertainty_deg": null,
        "is_experimental": false,
        "is_computed": false,
        "is_approximate": true,
        "equivalent_count": 1,
        "provenance_label_vi": "Chú giải từ nguồn dữ liệu",
        "provenance_label_en": "Source-derived annotation"
      }
    ],
    "vsepr_prediction": [
      {
        "id": "vsepr-AX2E2",
        "atom1_element": "H",
        "center_element": "O",
        "atom2_element": "H",
        "atom1_id": null,
        "center_atom_id": null,
        "atom2_id": null,
        "value_deg": 109.5,
        "coordinate_value_deg": null,
        "display_label": "<109.5°",
        "evidence_type": "ideal_vsepr",
        "source_name": "General VSEPR prediction",
        "source_url": null,
        "reference": null,
        "phase": null,
        "uncertainty_deg": null,
        "is_experimental": false,
        "is_computed": false,
        "is_approximate": true,
        "equivalent_count": 1,
        "provenance_label_vi": "Minh họa VSEPR lý tưởng hóa",
        "provenance_label_en": "Idealized VSEPR illustration"
      }
    ],
    "selection_reason": "A curated molecule-specific teaching reference is available."
  },
  "explanation": {
    "formula": "H2O",
    "level": "intermediate",
    "language": "vi",
    "sections": {
      "lewis": "H2O có 8 electron hoá trị, tổng điện tích hình thức bằng 0.",
      "ax_en": "2 miền liên kết và 2 miền cặp electron tự do, ký hiệu AX2E2.",
      "electron_geometry": "tứ diện",
      "molecular_geometry": "gấp khúc",
      "structure_property": "Phân tử phân cực do hình gấp khúc.",
      "learning_tip": "Cặp electron tự do đẩy mạnh hơn cặp electron liên kết.",
      "disclaimer": ""
    },
    "source": "openai",
    "fallback_reason": null,
    "prompt_version": "1.1",
    "facts_validated": true
  },
  "notices": {
    "offline_capable": true,
    "external_services_used": [],
    "warnings_vi": [
      "Mô hình 3D VSEPR lý tưởng hóa chỉ dùng để minh họa, không phải số liệu đo; góc hiển thị được đo từ chính tọa độ này.",
      "Bản ghi chuẩn nội bộ này đang chờ chuyên gia hóa học ký duyệt bên ngoài."
    ],
    "warnings_en": [
      "This idealized VSEPR model is an educational illustration, not measured data; displayed angles are measured from these coordinates.",
      "This internal golden record is awaiting external chemistry-expert sign-off."
    ],
    "external_service_statuses": [
      {
        "service": "NIST CCCBDB",
        "state": "disabled",
        "cache_hit": false,
        "message": null
      },
      {
        "service": "PubChem",
        "state": "not_found",
        "cache_hit": false,
        "message": "No PubChem CID was resolved for this identity."
      },
      {
        "service": "RDKit",
        "state": "disabled",
        "cache_hit": false,
        "message": null
      },
      {
        "service": "Deterministic chemistry",
        "state": "success",
        "cache_hit": false,
        "message": null
      }
    ]
  }
};

/** T-shaped ClF3: the multi-angle, experimental-geometry case. */
export const chlorineTrifluorideAnalysis: AnalysisResult = {
  "schema_version": "1.1",
  "molecule": {
    "id": "clf3",
    "formula": "ClF3",
    "name_vi": "Chlorine trifluoride",
    "name_en": "Chlorine trifluoride",
    "ax_en": "AX3E2",
    "molecular_geometry": "T-shaped",
    "molecular_geometry_vi": "chữ T",
    "review_status": "internal_golden_pending_expert_signoff",
    "charge": 0,
    "atom_inventory": {
      "Cl": 1,
      "F": 3
    },
    "central_atom": "Cl",
    "source": "curated",
    "confidence": "high",
    "pubchem_cid": null,
    "smiles": "Cl(F)(F)F",
    "canonical_identity": null,
    "inchi": null,
    "inchikey": null,
    "validation_status": "curated_verified",
    "cache_timestamp": null,
    "connectivity": {
      "atoms": [
        {
          "id": "a0",
          "element": "Cl"
        },
        {
          "id": "a1",
          "element": "F"
        },
        {
          "id": "a2",
          "element": "F"
        },
        {
          "id": "a3",
          "element": "F"
        }
      ],
      "bonds": [
        {
          "atom1_id": "a0",
          "atom2_id": "a1",
          "order": 1
        },
        {
          "atom1_id": "a0",
          "atom2_id": "a2",
          "order": 1
        },
        {
          "atom1_id": "a0",
          "atom2_id": "a3",
          "order": 1
        }
      ],
      "central_atom_id": "a0"
    }
  },
  "lewis": {
    "atoms": [
      {
        "id": "a0",
        "element": "Cl",
        "x": 212.5,
        "y": 140.0,
        "lone_pairs": 2,
        "formal_charge": 0
      },
      {
        "id": "a1",
        "element": "F",
        "x": 212.5,
        "y": 35.0,
        "lone_pairs": 3,
        "formal_charge": 0
      },
      {
        "id": "a2",
        "element": "F",
        "x": 212.5,
        "y": 245.0,
        "lone_pairs": 3,
        "formal_charge": 0
      },
      {
        "id": "a3",
        "element": "F",
        "x": 107.5,
        "y": 140.0,
        "lone_pairs": 3,
        "formal_charge": 0
      }
    ],
    "bonds": [
      {
        "id": "b0",
        "atom1_id": "a0",
        "atom2_id": "a1",
        "order": 1
      },
      {
        "id": "b1",
        "atom1_id": "a0",
        "atom2_id": "a2",
        "order": 1
      },
      {
        "id": "b2",
        "atom1_id": "a0",
        "atom2_id": "a3",
        "order": 1
      }
    ],
    "central_atom_id": "a0",
    "total_valence_electrons": 28,
    "resonance_forms": 1,
    "resonance_note_vi": null,
    "resonance_note_en": null,
    "resonance_structures": [],
    "exception_flags": {
      "electron_deficient": false,
      "expanded_octet": true,
      "odd_electron": false,
      "note_vi": "The Lewis representation uses an expanded octet."
    },
    "source": "curated",
    "confidence": "high",
    "review_status": "internal_golden_pending_expert_signoff"
  },
  "vsepr": {
    "bonding_domains": 3,
    "lone_pair_domains": 2,
    "steric_number": 5,
    "ax_en": "AX3E2",
    "electron_geometry": "trigonal bipyramidal",
    "electron_geometry_vi": "trigonal bipyramidal",
    "molecular_geometry": "T-shaped",
    "molecular_geometry_vi": "T-shaped",
    "ideal_angle": "~90°, 180°",
    "reference_angles": [
      {
        "display_label": "~90°, 180°",
        "source": "VSEPR teaching reference",
        "is_approximate": true,
        "note_vi": "Hai cặp tự do xích đạo nén nhẹ góc liên kết.",
        "note_en": "Two equatorial lone pairs slightly compress the bond angles."
      }
    ],
    "distortion_note_vi": "Hai cặp tự do xích đạo nén nhẹ góc liên kết.",
    "distortion_note_en": "Two equatorial lone pairs slightly compress the bond angles.",
    "teaching_note_vi": "Cl có thể là nguyên tử trung tâm trong hợp chất liên halogen; không được loại bằng quy tắc cứng.",
    "teaching_note_en": "Cl can be the central atom in an interhalogen compound; do not rule it out with a rigid rule.",
    "pedagogical_hybridization": "sp³d",
    "hybridization_warning_vi": "Nhãn lai hoá là mô hình sư phạm gần đúng theo VSEPR, không phải mô tả liên kết hiện đại đầy đủ.",
    "hybridization_warning_en": "The hybridization label is an approximate VSEPR-style pedagogical model, not a full modern description of bonding."
  },
  "properties": [
    {
      "key": "molar_mass",
      "category": "physical",
      "label_vi": "Khối lượng mol",
      "label_en": "Molar mass",
      "value": 92.444,
      "unit": "g/mol",
      "uncertainty": null,
      "conditions": null,
      "phase": null,
      "evidence_type": "computed",
      "source_name": "Standard atomic weights (IUPAC)",
      "source_name_en": "Standard atomic weights (IUPAC)",
      "source_name_vi": "Khối lượng nguyên tử chuẩn (IUPAC)",
      "source_reference": null,
      "source_url": null,
      "applicability": "applicable",
      "retrieved_at": null,
      "notes_vi": null,
      "notes_en": null,
      "observations": []
    },
    {
      "key": "central_atom_electronegativity",
      "category": "structural",
      "label_vi": "Độ âm điện nguyên tử trung tâm",
      "label_en": "Central-atom electronegativity",
      "value": 3.16,
      "unit": "Pauling",
      "uncertainty": null,
      "conditions": null,
      "phase": null,
      "evidence_type": "deterministic",
      "source_name": "Deterministic chemistry engine",
      "source_reference": null,
      "source_url": null,
      "applicability": "applicable",
      "retrieved_at": null,
      "notes_vi": null,
      "notes_en": null,
      "observations": []
    },
    {
      "key": "polarity",
      "category": "chemical",
      "label_vi": "Nhận xét về độ phân cực",
      "label_en": "Polarity note",
      "value": "The molecule is polar because of its T-shape.",
      "value_vi": "Phân tử phân cực do hình chữ T.",
      "value_en": "The molecule is polar because of its T-shape.",
      "unit": null,
      "uncertainty": null,
      "conditions": null,
      "phase": null,
      "evidence_type": "curated",
      "source_name": "Curated teaching record",
      "source_reference": null,
      "source_url": null,
      "applicability": "applicable",
      "retrieved_at": null,
      "notes_vi": null,
      "notes_en": null,
      "observations": []
    }
  ],
  "structure3d": {
    "format": "coordinates",
    "atoms": [
      {
        "id": "a0",
        "element": "Cl",
        "x": 0.0,
        "y": 0.0,
        "z": 0.0
      },
      {
        "id": "a1",
        "element": "F",
        "x": 1.697,
        "y": 0.0,
        "z": 0.0
      },
      {
        "id": "a2",
        "element": "F",
        "x": -1.6902816880020766,
        "y": -0.15085362178235073,
        "z": 0.0
      },
      {
        "id": "a3",
        "element": "F",
        "x": 0.0710524538871966,
        "y": -1.595418612401337,
        "z": 2.220446049250313e-16
      }
    ],
    "bonds": [
      {
        "atom1_id": "a0",
        "atom2_id": "a1",
        "order": 1
      },
      {
        "atom1_id": "a0",
        "atom2_id": "a2",
        "order": 1
      },
      {
        "atom1_id": "a0",
        "atom2_id": "a3",
        "order": 1
      }
    ],
    "data": null,
    "source": "experimental_geometry",
    "source_label": "NIST CCCBDB experimental gas-phase geometry",
    "evidence_type": "experimental",
    "geometry_evidence": {
      "id": "nist-cccbdb-clf3-2001muller",
      "evidence_type": "experimental",
      "provider": "nist_cccbdb",
      "source_name": "NIST CCCBDB",
      "source_reference": "2001Muller",
      "source_url": "https://cccbdb.nist.gov/expgeom2x.asp?casno=7790912&charge=0",
      "source_comments": "Experimental gas-phase T-shaped C2v structure listed by NIST CCCBDB from H. S. P. Müller et al., Phys. Chem. Chem. Phys. 3, 1570 (2001). Internal coordinates: r(Cl-F eq) = 1.597 Å, r(Cl-F ax) = 1.697 Å, ∠(F ax-Cl-F eq) = 87.45°, ∠(F ax-Cl-F ax) = 174.9° (by symmetry assuming planarity).",
      "retrieved_at": "2026-08-01T00:00:00Z",
      "phase": "gas",
      "electronic_state": "X 1A1",
      "conformation": "equilibrium",
      "point_group": "C2v",
      "units": "angstrom",
      "bond_lengths": [
        {
          "label": "Cl–F axial",
          "value_angstrom": 1.697,
          "uncertainty_angstrom": null,
          "equivalent_count": 2
        },
        {
          "label": "Cl–F equatorial",
          "value_angstrom": 1.597,
          "uncertainty_angstrom": null,
          "equivalent_count": 1
        }
      ],
      "bond_length_count": 3,
      "bond_angle_count": 3,
      "dihedral_count": 0,
      "coordinates_are_fitted": true,
      "max_length_deviation_angstrom": 4.440892098500626e-16,
      "max_angle_deviation_deg": 2.842170943040401e-14,
      "is_experimental": true,
      "is_computed": false,
      "is_ideal": false,
      "provenance_label_vi": "Phép đo thực nghiệm",
      "provenance_label_en": "Experimental measurement"
    },
    "is_illustrative": false,
    "is_computed": false,
    "is_experimental": true,
    "pubchem_cid": null,
    "central_atom_id": "a0",
    "reference_bond_angle": null,
    "angle_annotations": [
      {
        "id": "angle-0",
        "atom1_id": "a2",
        "center_atom_id": "a0",
        "atom2_id": "a3",
        "value_deg": 87.45,
        "coordinate_value_deg": 87.45,
        "source_value_deg": 87.45,
        "deviation_deg": 0.0,
        "uncertainty_deg": null,
        "display_label": "87.45°",
        "category": "measured",
        "evidence_type": "experimental",
        "source": "NIST CCCBDB experimental gas-phase geometry",
        "source_reference": "2001Muller",
        "source_url": "https://cccbdb.nist.gov/expgeom2x.asp?casno=7790912&charge=0",
        "phase": "gas",
        "is_approximate": false,
        "equivalent_count": 2,
        "note_vi": "Góc được tính trực tiếp từ tọa độ đang hiển thị.",
        "note_en": "Angle calculated directly from the rendered coordinates."
      },
      {
        "id": "angle-1",
        "atom1_id": "a1",
        "center_atom_id": "a0",
        "atom2_id": "a2",
        "value_deg": 174.9,
        "coordinate_value_deg": 174.90000000000003,
        "source_value_deg": 174.9,
        "deviation_deg": 2.842170943040401e-14,
        "uncertainty_deg": null,
        "display_label": "174.90°",
        "category": "measured",
        "evidence_type": "experimental",
        "source": "NIST CCCBDB experimental gas-phase geometry",
        "source_reference": "2001Muller",
        "source_url": "https://cccbdb.nist.gov/expgeom2x.asp?casno=7790912&charge=0",
        "phase": "gas",
        "is_approximate": false,
        "equivalent_count": 1,
        "note_vi": "Góc được tính trực tiếp từ tọa độ đang hiển thị.",
        "note_en": "Angle calculated directly from the rendered coordinates."
      }
    ],
    "electron_domains": [
      {
        "id": "bond-domain-0",
        "center_atom_id": "a0",
        "kind": "bonding",
        "occupancy": 2,
        "direction": {
          "x": 1.0,
          "y": 0.0,
          "z": 0.0
        },
        "position": {
          "x": 0.8485,
          "y": 0.0,
          "z": 0.0
        },
        "source": "NIST CCCBDB experimental gas-phase geometry",
        "is_illustrative": true,
        "label_vi": "Miền electron liên kết",
        "label_en": "Bonding electron domain"
      },
      {
        "id": "bond-domain-1",
        "center_atom_id": "a0",
        "kind": "bonding",
        "occupancy": 2,
        "direction": {
          "x": -0.9960410654107696,
          "y": -0.08889429686644118,
          "z": 0.0
        },
        "position": {
          "x": -0.8451408440010383,
          "y": -0.07542681089117537,
          "z": 0.0
        },
        "source": "NIST CCCBDB experimental gas-phase geometry",
        "is_illustrative": true,
        "label_vi": "Miền electron liên kết",
        "label_en": "Bonding electron domain"
      },
      {
        "id": "bond-domain-2",
        "center_atom_id": "a0",
        "kind": "bonding",
        "occupancy": 2,
        "direction": {
          "x": 0.04449120468828841,
          "y": -0.9990097760809875,
          "z": 1.3903857540703275e-16
        },
        "position": {
          "x": 0.0355262269435983,
          "y": -0.7977093062006685,
          "z": 1.1102230246251565e-16
        },
        "source": "NIST CCCBDB experimental gas-phase geometry",
        "is_illustrative": true,
        "label_vi": "Miền electron liên kết",
        "label_en": "Bonding electron domain"
      },
      {
        "id": "lone-pair-0",
        "center_atom_id": "a0",
        "kind": "lone_pair",
        "occupancy": 2,
        "direction": {
          "x": -0.5000110003630134,
          "y": 0.8660190526287391,
          "z": 0.0
        },
        "position": {
          "x": -0.5750126504174653,
          "y": 0.9959219105230499,
          "z": 0.0
        },
        "source": "illustrative VSEPR orientation",
        "is_illustrative": true,
        "label_vi": "Miền cặp electron tự do (minh họa)",
        "label_en": "Lone-pair electron domain (illustrative)"
      },
      {
        "id": "lone-pair-1",
        "center_atom_id": "a0",
        "kind": "lone_pair",
        "occupancy": 2,
        "direction": {
          "x": -0.5000110003630134,
          "y": -0.8660190526287391,
          "z": 0.0
        },
        "position": {
          "x": -0.5750126504174653,
          "y": -0.9959219105230499,
          "z": 0.0
        },
        "source": "illustrative VSEPR orientation",
        "is_illustrative": true,
        "label_vi": "Miền cặp electron tự do (minh họa)",
        "label_en": "Lone-pair electron domain (illustrative)"
      }
    ],
    "warning_vi": "Tọa độ nguyên tử là hình học gas đo được từ NIST CCCBDB; các miền cặp electron tự do vẫn chỉ là lớp minh họa VSEPR.",
    "warning_en": "Atomic coordinates are an experimental gas geometry from NIST CCCBDB; lone-pair domains remain illustrative VSEPR overlays."
  },
  "bond_angles": {
    "preferred": [
      {
        "id": "coordinate-angle-0",
        "atom1_element": "F",
        "center_element": "Cl",
        "atom2_element": "F",
        "atom1_id": "a2",
        "center_atom_id": "a0",
        "atom2_id": "a3",
        "value_deg": 87.45,
        "coordinate_value_deg": 87.45,
        "display_label": "87.45°",
        "evidence_type": "experimental",
        "source_name": "NIST CCCBDB",
        "source_url": "https://cccbdb.nist.gov/expgeom2x.asp?casno=7790912&charge=0",
        "reference": "2001Muller",
        "phase": "gas",
        "uncertainty_deg": null,
        "is_experimental": true,
        "is_computed": false,
        "is_approximate": false,
        "equivalent_count": 2,
        "provenance_label_vi": "Phép đo thực nghiệm",
        "provenance_label_en": "Experimental measurement"
      },
      {
        "id": "coordinate-angle-1",
        "atom1_element": "F",
        "center_element": "Cl",
        "atom2_element": "F",
        "atom1_id": "a1",
        "center_atom_id": "a0",
        "atom2_id": "a2",
        "value_deg": 174.9,
        "coordinate_value_deg": 174.90000000000003,
        "display_label": "174.90°",
        "evidence_type": "experimental",
        "source_name": "NIST CCCBDB",
        "source_url": "https://cccbdb.nist.gov/expgeom2x.asp?casno=7790912&charge=0",
        "reference": "2001Muller",
        "phase": "gas",
        "uncertainty_deg": null,
        "is_experimental": true,
        "is_computed": false,
        "is_approximate": false,
        "equivalent_count": 1,
        "provenance_label_vi": "Phép đo thực nghiệm",
        "provenance_label_en": "Experimental measurement"
      }
    ],
    "experimental": [
      {
        "id": "coordinate-angle-0",
        "atom1_element": "F",
        "center_element": "Cl",
        "atom2_element": "F",
        "atom1_id": "a2",
        "center_atom_id": "a0",
        "atom2_id": "a3",
        "value_deg": 87.45,
        "coordinate_value_deg": 87.45,
        "display_label": "87.45°",
        "evidence_type": "experimental",
        "source_name": "NIST CCCBDB",
        "source_url": "https://cccbdb.nist.gov/expgeom2x.asp?casno=7790912&charge=0",
        "reference": "2001Muller",
        "phase": "gas",
        "uncertainty_deg": null,
        "is_experimental": true,
        "is_computed": false,
        "is_approximate": false,
        "equivalent_count": 2,
        "provenance_label_vi": "Phép đo thực nghiệm",
        "provenance_label_en": "Experimental measurement"
      },
      {
        "id": "coordinate-angle-1",
        "atom1_element": "F",
        "center_element": "Cl",
        "atom2_element": "F",
        "atom1_id": "a1",
        "center_atom_id": "a0",
        "atom2_id": "a2",
        "value_deg": 174.9,
        "coordinate_value_deg": 174.90000000000003,
        "display_label": "174.90°",
        "evidence_type": "experimental",
        "source_name": "NIST CCCBDB",
        "source_url": "https://cccbdb.nist.gov/expgeom2x.asp?casno=7790912&charge=0",
        "reference": "2001Muller",
        "phase": "gas",
        "uncertainty_deg": null,
        "is_experimental": true,
        "is_computed": false,
        "is_approximate": false,
        "equivalent_count": 1,
        "provenance_label_vi": "Phép đo thực nghiệm",
        "provenance_label_en": "Experimental measurement"
      }
    ],
    "coordinate_derived": [
      {
        "id": "coordinate-angle-0",
        "atom1_element": "F",
        "center_element": "Cl",
        "atom2_element": "F",
        "atom1_id": "a2",
        "center_atom_id": "a0",
        "atom2_id": "a3",
        "value_deg": 87.45,
        "coordinate_value_deg": 87.45,
        "display_label": "87.45°",
        "evidence_type": "experimental",
        "source_name": "NIST CCCBDB",
        "source_url": "https://cccbdb.nist.gov/expgeom2x.asp?casno=7790912&charge=0",
        "reference": "2001Muller",
        "phase": "gas",
        "uncertainty_deg": null,
        "is_experimental": true,
        "is_computed": false,
        "is_approximate": false,
        "equivalent_count": 2,
        "provenance_label_vi": "Phép đo thực nghiệm",
        "provenance_label_en": "Experimental measurement"
      },
      {
        "id": "coordinate-angle-1",
        "atom1_element": "F",
        "center_element": "Cl",
        "atom2_element": "F",
        "atom1_id": "a1",
        "center_atom_id": "a0",
        "atom2_id": "a2",
        "value_deg": 174.9,
        "coordinate_value_deg": 174.90000000000003,
        "display_label": "174.90°",
        "evidence_type": "experimental",
        "source_name": "NIST CCCBDB",
        "source_url": "https://cccbdb.nist.gov/expgeom2x.asp?casno=7790912&charge=0",
        "reference": "2001Muller",
        "phase": "gas",
        "uncertainty_deg": null,
        "is_experimental": true,
        "is_computed": false,
        "is_approximate": false,
        "equivalent_count": 1,
        "provenance_label_vi": "Phép đo thực nghiệm",
        "provenance_label_en": "Experimental measurement"
      }
    ],
    "curated_reference": [],
    "vsepr_prediction": [
      {
        "id": "vsepr-AX3E2",
        "atom1_element": "F",
        "center_element": "Cl",
        "atom2_element": "F",
        "atom1_id": null,
        "center_atom_id": null,
        "atom2_id": null,
        "value_deg": 90.0,
        "coordinate_value_deg": null,
        "display_label": "~90°, 180°",
        "evidence_type": "ideal_vsepr",
        "source_name": "General VSEPR prediction",
        "source_url": null,
        "reference": null,
        "phase": null,
        "uncertainty_deg": null,
        "is_experimental": false,
        "is_computed": false,
        "is_approximate": true,
        "equivalent_count": 1,
        "provenance_label_vi": "Minh họa VSEPR lý tưởng hóa",
        "provenance_label_en": "Idealized VSEPR illustration"
      }
    ],
    "selection_reason": "Experimental geometry from NIST CCCBDB is the highest-priority evidence; 2 inequivalent angle(s) were measured."
  },
  "explanation": null,
  "notices": {
    "offline_capable": true,
    "external_services_used": [],
    "warnings_vi": [
      "Tọa độ nguyên tử là hình học gas đo được từ NIST CCCBDB; các miền cặp electron tự do vẫn chỉ là lớp minh họa VSEPR.",
      "Bản ghi chuẩn nội bộ này đang chờ chuyên gia hóa học ký duyệt bên ngoài."
    ],
    "warnings_en": [
      "Atomic coordinates are an experimental gas geometry from NIST CCCBDB; lone-pair domains remain illustrative VSEPR overlays.",
      "This internal golden record is awaiting external chemistry-expert sign-off."
    ],
    "external_service_statuses": [
      {
        "service": "Local geometry snapshot",
        "state": "cache_hit",
        "cache_hit": true,
        "message": null
      }
    ]
  }
};
