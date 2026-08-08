import { useCallback, useEffect, useRef, useState } from "react";
import { analyzeMolecule } from "../api/analysisApi";
import { getApiErrorDetail, isCanceledError, type ApiErrorDetail } from "../api/client";
import type { AnalysisRequest, AnalysisResult } from "../types/analysis";

export function useAnalyzeMolecule() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<ApiErrorDetail | null>(null);
  const [isLoading, setLoading] = useState(false);
  const inFlight = useRef<AbortController | null>(null);
  useEffect(() => () => inFlight.current?.abort(), []);
  const run = useCallback(async (request: AnalysisRequest) => {
    // Supersede any analysis still in flight. React Strict Mode double-invokes
    // the page effect in development, and retyping a formula can otherwise race
    // a stale response into view; only the newest request may settle state.
    inFlight.current?.abort();
    const controller = new AbortController();
    inFlight.current = controller;
    setLoading(true); setError(null);
    try { const data = await analyzeMolecule(request, controller.signal); setResult(data); return data; }
    catch (caught) { if (!isCanceledError(caught)) setError(getApiErrorDetail(caught)); return null; }
    finally { if (inFlight.current === controller) { inFlight.current = null; setLoading(false); } }
  }, []);
  return { result, error, isLoading, run, setResult };
}
