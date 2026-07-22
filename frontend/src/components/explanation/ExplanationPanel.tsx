import { useState } from "react";
import { useI18n } from "../../i18n";
import { useExplanation } from "../../hooks/useExplanation";
import type { Explanation, ExplanationLevel } from "../../types/explanation";
import AIDisclaimer from "./AIDisclaimer";
import ExplanationLevelSelector from "./ExplanationLevelSelector";
import ExplanationSection from "./ExplanationSection";

export default function ExplanationPanel({ moleculeId, initial }: { moleculeId: string; initial: Explanation | null }) {
  const { t } = useI18n();
  const { explanation, isLoading, error, regenerate } = useExplanation(initial); const [level, setLevel] = useState<ExplanationLevel>(initial?.level || "intermediate");
  const sectionTitle = (key: string) => t(`explanation.section.${key}`);
  if (!explanation) return <div><p>{t("explanation.empty")}</p><ExplanationLevelSelector value={level} onChange={setLevel} /><button onClick={() => void regenerate(moleculeId, level)}>{t("explanation.generate")}</button>{error && <p className="error-message">{error}</p>}</div>;
  return <div className="explanation-panel"><div className="explanation-actions"><ExplanationLevelSelector value={level} onChange={setLevel} disabled={isLoading} /><button onClick={() => void regenerate(moleculeId, level)} disabled={isLoading}>{isLoading ? t("explanation.generating") : t("explanation.regenerate")}</button><button className="secondary-button" onClick={() => void navigator.clipboard?.writeText(Object.values(explanation.sections).join("\n\n"))}>{t("explanation.copy")}</button></div>{explanation.fallback_reason && <p className="offline-notice">{explanation.fallback_reason}</p>}{Object.entries(explanation.sections).map(([key, value]) => <ExplanationSection key={key} title={sectionTitle(key)}>{value}</ExplanationSection>)}<AIDisclaimer source={explanation.source} />{error && <p className="error-message">{error}</p>}</div>;
}
