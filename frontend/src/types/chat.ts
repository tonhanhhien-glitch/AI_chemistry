export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  reply: string;
  source: "openrouter" | "openai" | "deterministic_fallback";
  fallback_reason: string | null;
}
