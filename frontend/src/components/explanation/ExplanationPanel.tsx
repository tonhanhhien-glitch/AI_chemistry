import { useI18n } from "../../i18n";
import { useExplanation } from "../../hooks/useExplanation";
import type { Explanation } from "../../types/explanation";
import ExplanationSection from "./ExplanationSection";

export default function ExplanationPanel({ moleculeId, formula, pubchemCid, initial }: { moleculeId: string; formula: string; pubchemCid: number | null; initial: Explanation | null }) {
  const { t, lang } = useI18n();
  const { explanation, isLoading, error, regenerate } = useExplanation(initial);
  const sectionTitle = (key: string) => t(`explanation.section.${key}`);
  // /analyze no longer waits on the model, so this button is where the AI call
  // happens and it must show that it is running.
  if (!explanation) return <div><p>{t("explanation.empty")}</p><button disabled={isLoading} onClick={() => void regenerate(moleculeId, formula, pubchemCid, "intermediate", lang)}>{isLoading ? <><span className="loader" />{t("explanation.generating")}</> : t("explanation.generate")}</button>{error && <p className="error-message">{error}</p>}</div>;
  return <div className="explanation-panel">{Object.entries(explanation.sections).map(([key, value]) => <ExplanationSection key={key} title={sectionTitle(key)}>{value}</ExplanationSection>)}{error && <p className="error-message">{error}</p>}</div>;
}
