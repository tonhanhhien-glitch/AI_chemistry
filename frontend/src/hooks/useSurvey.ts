import { useState } from "react";
import { getApiErrorMessage } from "../api/client";
import { submitSurvey } from "../api/surveyApi";
import type { SurveySubmission } from "../types/survey";

export function useSurvey() {
  const [message, setMessage] = useState("");
  const [isLoading, setLoading] = useState(false);
  async function submit(payload: SurveySubmission) {
    setLoading(true); setMessage("");
    try { const response = await submitSurvey(payload); localStorage.setItem("vsepr-session", response.session_id); setMessage(response.message_vi); return true; }
    catch (caught) { setMessage(getApiErrorMessage(caught)); return false; }
    finally { setLoading(false); }
  }
  return { submit, message, isLoading };
}
