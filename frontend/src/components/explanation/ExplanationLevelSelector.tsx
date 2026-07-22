import { useI18n } from "../../i18n";
import type { ExplanationLevel } from "../../types/explanation";

export default function ExplanationLevelSelector({ value, onChange, disabled = false }: { value: ExplanationLevel; onChange: (value: ExplanationLevel) => void; disabled?: boolean }) {
  const { t } = useI18n();
  return <fieldset className="level-selector" disabled={disabled}><legend>{t("explanation.level.legend")}</legend>{([["basic", "explanation.level.basic"], ["intermediate", "explanation.level.intermediate"], ["advanced", "explanation.level.advanced"]] as const).map(([level, labelKey]) => <label key={level}><input type="radio" name="level" value={level} checked={value === level} onChange={() => onChange(level)} />{t(labelKey)}</label>)}</fieldset>;
}
