import type { Lang } from "../i18n";
import type { ChatMessage, ChatResponse } from "../types/chat";
import { apiClient } from "./client";

export async function sendChatMessage(moleculeId: string, formula: string, pubchemCid: number | null, messages: ChatMessage[], language: Lang): Promise<ChatResponse> {
  return (await apiClient.post<ChatResponse>("/chat", { molecule_id: moleculeId, formula, pubchem_cid: pubchemCid, messages, language })).data;
}
