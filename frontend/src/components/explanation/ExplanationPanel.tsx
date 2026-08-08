import { useI18n } from "../../i18n";
import { useExplanation } from "../../hooks/useExplanation";
import type { Explanation } from "../../types/explanation";
import ExplanationSection from "./ExplanationSection";

export default function ExplanationPanel({ moleculeId, formula, pubchemCid, initial }: { moleculeId: string; formula: string; pubchemCid: number | null; initial: Explanation | null }) {
  const { t, lang } = useI18n();
  const { explanation, error, regenerate } = useExplanation(initial);
  const sectionTitle = (key: string) => t(`explanation.section.${key}`);
  if (!explanation) return <div><p>{t("explanation.empty")}</p><button onClick={() => void regenerate(moleculeId, formula, pubchemCid, "intermediate", lang)}>{t("explanation.generate")}</button>{error && <p className="error-message">{error}</p>}</div>;
  return <div className="explanation-panel">{Object.entries(explanation.sections).map(([key, value]) => <ExplanationSection key={key} title={sectionTitle(key)}>{value}</ExplanationSection>)}{error && <p className="error-message">{error}</p>}</div>;
}
