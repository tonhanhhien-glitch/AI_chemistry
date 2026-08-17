import type { PropertyBundle } from "../types/properties";
import { apiClient } from "./client";

export interface PropertyRequest {
  formula?: string;
  molecule_id?: string;
  pubchem_cid?: number;
}

/**
 * Physical and chemical properties are fetched separately from `/analyze` so the
 * deterministic analysis is never blocked behind several external requests.
 */
export async function fetchProperties(request: PropertyRequest, signal?: AbortSignal): Promise<PropertyBundle> {
  return (await apiClient.post<PropertyBundle>("/properties", request, { signal, timeout: 30_000 })).data;
}
