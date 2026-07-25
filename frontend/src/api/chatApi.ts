import type { Lang } from "../i18n";
import type { ChatMessage, ChatResponse } from "../types/chat";
import { apiClient } from "./client";

export async function sendChatMessage(moleculeId: string, messages: ChatMessage[], language: Lang): Promise<ChatResponse> {
  return (await apiClient.post<ChatResponse>("/chat", { molecule_id: moleculeId, messages, language })).data;
}
