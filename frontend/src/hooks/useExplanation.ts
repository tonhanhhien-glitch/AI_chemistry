import { useState } from "react";
import { requestExplanation } from "../api/explanationApi";
import { getApiErrorMessage } from "../api/client";
import type { Explanation, ExplanationLevel } from "../types/explanation";

export function useExplanation(initial: Explanation | null) {
  const [explanation, setExplanation] = useState(initial);
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState("");
  async function regenerate(moleculeId: string, level: ExplanationLevel) {
    setLoading(true); setError("");
    try { setExplanation(await requestExplanation(moleculeId, level)); }
    catch (caught) { setError(getApiErrorMessage(caught)); }
    finally { setLoading(false); }
  }
  return { explanation, isLoading, error, regenerate };
}
