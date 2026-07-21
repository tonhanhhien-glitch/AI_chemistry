import { useState } from "react";
import { getApiErrorMessage } from "../api/client";
import { submitFeedback } from "../api/feedbackApi";
import type { FeedbackSubmission } from "../types/feedback";

export function useFeedback() {
  const [status, setStatus] = useState("");
  const [isLoading, setLoading] = useState(false);
  async function submit(payload: FeedbackSubmission) {
    setLoading(true); setStatus("");
    try { const result = await submitFeedback(payload); localStorage.setItem("vsepr-session", result.session_id); setStatus(result.message_vi); }
    catch (caught) { setStatus(getApiErrorMessage(caught)); }
    finally { setLoading(false); }
  }
  return { submit, status, isLoading };
}
