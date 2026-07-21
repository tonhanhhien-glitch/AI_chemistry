import type { FeedbackSubmission, PersistenceResponse } from "../types/feedback";
import { apiClient } from "./client";

export async function submitFeedback(payload: FeedbackSubmission): Promise<PersistenceResponse> {
  return (await apiClient.post<PersistenceResponse>("/feedback", payload)).data;
}
