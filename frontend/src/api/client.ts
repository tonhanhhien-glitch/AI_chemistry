import axios, { AxiosError } from "axios";

interface ApiErrorBody {
  detail?: string | {
    code?: string;
    message?: string;
  };
}

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
  timeout: 10_000,
  headers: {
    Accept: "application/json",
  },
});

export function getApiErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const body = error.response?.data as ApiErrorBody | undefined;
    if (typeof body?.detail === "string") {
      return body.detail;
    }
    if (body?.detail?.message) {
      return body.detail.message;
    }
    if (error.code === "ECONNABORTED") {
      return "Yêu cầu đã hết thời gian chờ. Vui lòng thử lại.";
    }
  }

  return "Không thể kết nối tới máy chủ. Vui lòng thử lại.";
}
