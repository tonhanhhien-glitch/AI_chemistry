export interface SurveySubmission {
  session_id?: string;
  consent: boolean;
  phase: "pre" | "post" | "likert";
  answers: Record<string, number | string | boolean>;
}
