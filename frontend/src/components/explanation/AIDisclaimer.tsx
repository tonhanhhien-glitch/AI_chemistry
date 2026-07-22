import { useI18n } from "../../i18n";

export default function AIDisclaimer({ source }: { source: "claude" | "deterministic_fallback" }) {
  const { t } = useI18n();
  return <p className="ai-disclaimer"><strong>{source === "claude" ? t("explanation.disclaimer.claude") : t("explanation.disclaimer.deterministic")}</strong> {t("explanation.disclaimer.body")}</p>;
}
