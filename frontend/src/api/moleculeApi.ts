import type { MoleculeSummary } from "../types/molecule";
import { apiClient } from "./client";

export async function getExamples(): Promise<MoleculeSummary[]> {
  return (await apiClient.get<MoleculeSummary[]>("/molecules/examples")).data;
}

export async function searchMolecules(q: string): Promise<MoleculeSummary[]> {
  const response = await apiClient.get<{ query: string; results: MoleculeSummary[] }>("/molecules/search", { params: { q } });
  return response.data.results;
}

export interface VseprRuleRecord {
  ax_en: string;
  bonding_domains: number;
  lone_pair_domains: number;
  electron_geometry: string;
  electron_geometry_vi: string;
  molecular_geometry: string;
  molecular_geometry_vi: string;
  ideal_angle: string;
  teaching_note_vi: string;
}

export async function getVseprRules(): Promise<VseprRuleRecord[]> {
  return (await apiClient.get<{ rules: VseprRuleRecord[] }>("/rules/vsepr")).data.rules;
}
