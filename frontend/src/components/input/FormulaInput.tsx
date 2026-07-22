import type { FormEvent } from "react";
import { useI18n } from "../../i18n";

export default function FormulaInput({ value, onChange, onSubmit, loading = false }: { value: string; onChange: (value: string) => void; onSubmit: () => void; loading?: boolean }) {
  const { t } = useI18n();
  function submit(event: FormEvent) { event.preventDefault(); onSubmit(); }
  return <form className="formula-form" onSubmit={submit}><label htmlFor="formula">{t("formulaInput.label")}</label><div className="search-row"><input id="formula" value={value} onChange={(event) => onChange(event.target.value)} maxLength={80} placeholder={t("formulaInput.placeholder")} autoComplete="off" /><button disabled={loading}>{loading ? t("formulaInput.analyzing") : t("formulaInput.analyze")}</button></div><small>{t("formulaInput.help")}</small></form>;
}
