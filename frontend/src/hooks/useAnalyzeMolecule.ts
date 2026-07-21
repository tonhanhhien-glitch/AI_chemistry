import { useCallback, useState } from "react";
import { analyzeMolecule } from "../api/analysisApi";
import { getApiErrorDetail, type ApiErrorDetail } from "../api/client";
import type { AnalysisRequest, AnalysisResult } from "../types/analysis";

export function useAnalyzeMolecule() {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<ApiErrorDetail | null>(null);
  const [isLoading, setLoading] = useState(false);
  const run = useCallback(async (request: AnalysisRequest) => {
    setLoading(true); setError(null);
    try { const data = await analyzeMolecule(request); setResult(data); return data; }
    catch (caught) { setError(getApiErrorDetail(caught)); return null; }
    finally { setLoading(false); }
  }, []);
  return { result, error, isLoading, run, setResult };
}
