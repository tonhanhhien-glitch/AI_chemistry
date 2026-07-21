import type { PersistenceResponse } from "../types/feedback";
import type { SurveySubmission } from "../types/survey";
import { apiClient } from "./client";

export async function submitSurvey(payload: SurveySubmission): Promise<PersistenceResponse> {
  return (await apiClient.post<PersistenceResponse>("/survey", payload)).data;
}
