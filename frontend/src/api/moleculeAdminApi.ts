import type { AnalysisResult } from "../types/analysis";
import type {
  AdminSessionStatus,
  CompletenessReport,
  MoleculeAdminListItem,
  MoleculeAdminRecord,
  MoleculeAdminSavePayload,
  MoleculeAdminSaveResponse,
  MoleculeDraft,
  ValidationReport,
} from "../types/moleculeAdmin";
import { apiClient } from "./client";

export async function adminLogin(username: string, password: string): Promise<AdminSessionStatus> {
  return (await apiClient.post<AdminSessionStatus>("/admin/login", { username, password })).data;
}

export async function adminLogout(): Promise<AdminSessionStatus> {
  return (await apiClient.post<AdminSessionStatus>("/admin/logout")).data;
}

export async function adminSession(): Promise<AdminSessionStatus> {
  return (await apiClient.get<AdminSessionStatus>("/admin/session")).data;
}

export async function listAdminMolecules(q?: string): Promise<MoleculeAdminListItem[]> {
  const response = await apiClient.get<{ results: MoleculeAdminListItem[] }>("/admin/molecules", { params: q ? { q } : undefined });
  return response.data.results;
}

export async function getAdminMolecule(id: string): Promise<MoleculeAdminRecord> {
  return (await apiClient.get<MoleculeAdminRecord>(`/admin/molecules/${encodeURIComponent(id)}`)).data;
}

export async function createAdminMolecule(payload: MoleculeAdminSavePayload): Promise<MoleculeAdminSaveResponse> {
  return (await apiClient.post<MoleculeAdminSaveResponse>("/admin/molecules", payload)).data;
}

export async function updateAdminMolecule(id: string, payload: MoleculeAdminSavePayload): Promise<MoleculeAdminSaveResponse> {
  return (await apiClient.put<MoleculeAdminSaveResponse>(`/admin/molecules/${encodeURIComponent(id)}`, payload)).data;
}

export async function validateAdminMolecule(id: string, payload: MoleculeAdminSavePayload): Promise<ValidationReport> {
  return (await apiClient.post<ValidationReport>(`/admin/molecules/${encodeURIComponent(id)}/validate`, payload)).data;
}

export async function previewAdminMolecule(payload: MoleculeAdminSavePayload): Promise<AnalysisResult> {
  return (await apiClient.post<AnalysisResult>("/admin/molecules/preview", payload)).data;
}

export async function revertAdminMolecule(id: string): Promise<{ had_override: boolean; reverted_to_baseline: boolean }> {
  return (await apiClient.post(`/admin/molecules/${encodeURIComponent(id)}/revert`)).data;
}

export async function getAdminCompleteness(id: string): Promise<CompletenessReport> {
  return (await apiClient.get<CompletenessReport>(`/admin/molecules/${encodeURIComponent(id)}/completeness`)).data;
}

export async function generateAdminDraft(formula: string, charge: number, id?: string): Promise<MoleculeDraft> {
  return (await apiClient.post<MoleculeDraft>("/admin/molecules/draft", { formula, charge, id })).data;
}
