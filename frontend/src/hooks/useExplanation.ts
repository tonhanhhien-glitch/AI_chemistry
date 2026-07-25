import { useEffect, useState } from "react";
import { requestExplanation } from "../api/explanationApi";
import { getApiErrorMessage } from "../api/client";
import type { Lang } from "../i18n";
import type { Explanation, ExplanationLevel } from "../types/explanation";

export function useExplanation(initial: Explanation | null) {
  const [explanation, setExplanation] = useState(initial);
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState("");
  // Adopt a freshly fetched explanation (e.g. after a language switch re-runs
  // the analysis) instead of keeping the value captured at first render.
  useEffect(() => { setExplanation(initial); }, [initial]);
  async function regenerate(moleculeId: string, level: ExplanationLevel, language: Lang) {
    setLoading(true); setError("");
    try { setExplanation(await requestExplanation(moleculeId, level, language)); }
    catch (caught) { setError(getApiErrorMessage(caught)); }
    finally { setLoading(false); }
  }
  return { explanation, isLoading, error, regenerate };
}
