import type { Explanation, ExplanationLevel } from "../types/explanation";
import { apiClient } from "./client";

export async function requestExplanation(moleculeId: string, level: ExplanationLevel): Promise<Explanation> {
  return (await apiClient.post<Explanation>("/explain", { molecule_id: moleculeId, level, language: "vi" })).data;
}
