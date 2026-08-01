export interface VseprResult {
  bonding_domains: number;
  lone_pair_domains: number;
  steric_number: number;
  ax_en: string;
  electron_geometry: string;
  electron_geometry_vi: string;
  molecular_geometry: string;
  molecular_geometry_vi: string;
  ideal_angle: string;
  reference_angles: Array<{ display_label: string; source: string; is_approximate: boolean; note_vi: string | null; note_en: string | null }>;
  distortion_note_vi: string | null;
  distortion_note_en: string | null;
  teaching_note_vi: string;
  teaching_note_en: string;
  pedagogical_hybridization: string | null;
  hybridization_warning_vi: string | null;
  hybridization_warning_en: string | null;
}
