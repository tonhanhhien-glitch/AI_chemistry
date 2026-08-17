import { useCallback, useEffect, useRef, useState } from "react";
import { fetchProperties, type PropertyRequest } from "../api/propertiesApi";
import { getApiErrorDetail, isCanceledError, type ApiErrorDetail } from "../api/client";
import type { PropertyBundle } from "../types/properties";

/**
 * Lazily loads the property bundle, once, when the caller asks for it.
 *
 * The section is collapsed by default, so nothing is fetched until a student opens it;
 * a failure surfaces as an error state beside the rest of the analysis rather than
 * taking the page down with it.
 */
export function useProperties(request: PropertyRequest) {
  const [bundle, setBundle] = useState<PropertyBundle | null>(null);
  const [error, setError] = useState<ApiErrorDetail | null>(null);
  const [isLoading, setLoading] = useState(false);
  const inFlight = useRef<AbortController | null>(null);
  const requested = useRef(false);

  const key = `${request.molecule_id ?? ""}|${request.formula ?? ""}|${request.pubchem_cid ?? ""}`;
  useEffect(() => {
    requested.current = false;
    setBundle(null);
    setError(null);
  }, [key]);
  useEffect(() => () => inFlight.current?.abort(), []);

  const load = useCallback(async (force = false) => {
    if (requested.current && !force) return;
    requested.current = true;
    inFlight.current?.abort();
    const controller = new AbortController();
    inFlight.current = controller;
    setLoading(true); setError(null);
    try { setBundle(await fetchProperties(request, controller.signal)); }
    catch (caught) { if (!isCanceledError(caught)) { setError(getApiErrorDetail(caught)); requested.current = false; } }
    finally { if (inFlight.current === controller) { inFlight.current = null; setLoading(false); } }
  }, [request]);

  return { bundle, error, isLoading, load };
}
