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
  distortion_note_vi: string | null;
  teaching_note_vi: string;
  pedagogical_hybridization: string | null;
  hybridization_warning_vi: string | null;
}
