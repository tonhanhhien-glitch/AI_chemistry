export interface FeedbackSubmission {
  session_id?: string;
  molecule_id?: string;
  rating: number;
  category: "clarity" | "usefulness" | "chemistry_error" | "other";
  comment?: string;
}

export interface PersistenceResponse {
  accepted: boolean;
  session_id: string;
  message_vi: string;
}
