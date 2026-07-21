import type { ExplanationLevel } from "../../types/explanation";

export default function ExplanationLevelSelector({ value, onChange, disabled = false }: { value: ExplanationLevel; onChange: (value: ExplanationLevel) => void; disabled?: boolean }) {
  return <fieldset className="level-selector" disabled={disabled}><legend>Mức độ giải thích</legend>{([["basic", "Cơ bản"], ["intermediate", "Trung cấp"], ["advanced", "Nâng cao"]] as const).map(([level, label]) => <label key={level}><input type="radio" name="level" value={level} checked={value === level} onChange={() => onChange(level)} />{label}</label>)}</fieldset>;
}
