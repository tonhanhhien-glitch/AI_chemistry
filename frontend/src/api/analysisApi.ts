import type { AnalysisRequest, AnalysisResult } from "../types/analysis";
import { apiClient } from "./client";

export async function analyzeMolecule(request: AnalysisRequest, signal?: AbortSignal): Promise<AnalysisResult> {
  return (await apiClient.post<AnalysisResult>("/analyze", request, { signal })).data;
}
