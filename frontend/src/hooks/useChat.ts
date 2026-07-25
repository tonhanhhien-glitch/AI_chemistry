import { useCallback, useEffect, useState } from "react";
import { sendChatMessage } from "../api/chatApi";
import { getApiErrorMessage } from "../api/client";
import { useI18n } from "../i18n";
import type { ChatMessage } from "../types/chat";

export function useChat(moleculeId: string) {
  const { lang } = useI18n();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Start a fresh conversation whenever the analysed molecule changes.
  useEffect(() => { setMessages([]); setError(""); setLoading(false); }, [moleculeId]);

  const send = useCallback(async (text: string) => {
    const question = text.trim();
    if (!question) return;
    const history: ChatMessage[] = [...messages, { role: "user", content: question }];
    setMessages(history); setLoading(true); setError("");
    try {
      const answer = await sendChatMessage(moleculeId, history, lang);
      setMessages([...history, { role: "assistant", content: answer.reply }]);
    } catch (caught) {
      setError(getApiErrorMessage(caught));
    } finally {
      setLoading(false);
    }
  }, [lang, messages, moleculeId]);

  return { messages, isLoading, error, send };
}
