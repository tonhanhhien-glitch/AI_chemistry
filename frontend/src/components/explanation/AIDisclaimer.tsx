import { useI18n } from "../../i18n";
import type { Explanation } from "../../types/explanation";

export default function AIDisclaimer({ source }: { source: Explanation["source"] }) {
  const { t } = useI18n();
  // Any LLM provider (OpenRouter or its OpenAI fallback) reads as "AI"; only the
  // deterministic template gets the stronger wording.
  return <p className="ai-disclaimer"><strong>{source === "deterministic_fallback" ? t("explanation.disclaimer.deterministic") : t("explanation.disclaimer.ai")}</strong> {t("explanation.disclaimer.body")}</p>;
}
