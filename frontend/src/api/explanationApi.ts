import type { Lang } from "../i18n";
import type { Explanation, ExplanationLevel } from "../types/explanation";
import { apiClient } from "./client";

export async function requestExplanation(moleculeId: string, formula: string, pubchemCid: number | null, level: ExplanationLevel, language: Lang): Promise<Explanation> {
  return (await apiClient.post<Explanation>("/explain", { molecule_id: moleculeId, formula, pubchem_cid: pubchemCid, level, language })).data;
}
