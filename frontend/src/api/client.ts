import axios, { AxiosError } from "axios";

import { t } from "../i18n";

export interface ApiErrorDetail {
  code: string;
  message: string;
  candidates?: Array<{ id: string; formula: string; name_vi: string; name_en: string; cid?: number; charge?: number; canonical_smiles?: string | null; source?: string }>;
}

interface ApiErrorBody {
  detail?: string | Partial<ApiErrorDetail>;
}

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
  timeout: 15_000,
  headers: { Accept: "application/json", "Content-Type": "application/json" },
});

/**
 * Budget for the OpenRouter-backed endpoints (/explain, /chat). Free-tier model
 * latency is inherently unpredictable, so they get their own limit instead of
 * pushing the deterministic default up for every request.
 */
export const AI_TIMEOUT_MS = 45_000;

/** True when a request was superseded or unmounted, not when it actually failed. */
export function isCanceledError(error: unknown): boolean {
  return axios.isCancel(error);
}

export function getApiErrorDetail(error: unknown): ApiErrorDetail {
  if (error instanceof AxiosError) {
    const body = error.response?.data as ApiErrorBody | undefined;
    if (typeof body?.detail === "string") return { code: "API_ERROR", message: body.detail };
    if (body?.detail?.message) return {
      code: body.detail.code || "API_ERROR", message: body.detail.message,
      candidates: body.detail.candidates,
    };
    if (error.code === "ECONNABORTED") return { code: "TIMEOUT", message: t("api.error.timeout") };
  }
  return { code: "NETWORK_ERROR", message: t("api.error.network") };
}

export function getApiErrorMessage(error: unknown): string {
  return getApiErrorDetail(error).message;
}
