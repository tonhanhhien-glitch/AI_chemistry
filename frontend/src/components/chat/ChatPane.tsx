import { useEffect, useRef, useState } from "react";
import { useI18n } from "../../i18n";
import { useChat } from "../../hooks/useChat";

export default function ChatPane({ moleculeId, formula, pubchemCid }: { moleculeId: string; formula: string; pubchemCid: number | null }) {
  const { t } = useI18n();
  const { messages, isLoading, error, send } = useChat(moleculeId, formula, pubchemCid);
  const [draft, setDraft] = useState("");
  const logRef = useRef<HTMLDivElement>(null);

  useEffect(() => { if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight; }, [messages, isLoading]);

  const suggestions = [t("chat.suggest.1"), t("chat.suggest.2"), t("chat.suggest.3")];

  function ask(text: string) {
    if (isLoading) return;
    void send(text);
    setDraft("");
  }

  return (
    <div className="chat-pane-inner">
      <div className="chat-log" ref={logRef} aria-live="polite">
        {messages.length === 0 ? (
          <div className="chat-intro">
            <p>{t("chat.empty", { formula })}</p>
            <div className="chat-suggestions">
              {suggestions.map((suggestion) => (
                <button key={suggestion} type="button" className="chat-chip" onClick={() => ask(suggestion)}>{suggestion}</button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message, index) => (
            <p key={index} className={`chat-msg chat-${message.role}`}>{message.content}</p>
          ))
        )}
        {isLoading && <p className="chat-msg chat-assistant chat-typing" aria-label={t("chat.sending")}><span /><span /><span /></p>}
        {error && <p className="error-message chat-error">{error}</p>}
      </div>
      <form className="chat-input-row" onSubmit={(event) => { event.preventDefault(); ask(draft); }}>
        <input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder={t("chat.placeholder")} aria-label={t("chat.placeholder")} maxLength={2000} />
        <button type="submit" disabled={isLoading || !draft.trim()}>{isLoading ? t("chat.sending") : t("chat.send")}</button>
      </form>
      <p className="chat-disclaimer">{t("chat.disclaimer")}</p>
    </div>
  );
}
