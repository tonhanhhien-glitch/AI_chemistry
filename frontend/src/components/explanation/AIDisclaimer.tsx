import { useI18n } from "../../i18n";

export default function AIDisclaimer({ source }: { source: "openrouter" | "deterministic_fallback" }) {
  const { t } = useI18n();
  return <p className="ai-disclaimer"><strong>{source === "openrouter" ? t("explanation.disclaimer.ai") : t("explanation.disclaimer.deterministic")}</strong> {t("explanation.disclaimer.body")}</p>;
}
