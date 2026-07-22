import { useI18n } from "../../i18n";

export default function AtomLabelToggle({ checked, onChange }: { checked: boolean; onChange: (value: boolean) => void }) {
  const { t } = useI18n();
  return <label className="check-control"><input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} /> {t("viewer3d.atomLabels")}</label>;
}
