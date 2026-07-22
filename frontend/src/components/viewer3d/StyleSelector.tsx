import { useI18n } from "../../i18n";

export type ViewerStyle = "stick" | "sphere";

export default function StyleSelector({ value, onChange }: { value: ViewerStyle; onChange: (value: ViewerStyle) => void }) {
  const { t } = useI18n();
  return <label className="inline-control">{t("viewer3d.styleLabel")}<select value={value} onChange={(event) => onChange(event.target.value as ViewerStyle)}><option value="stick">{t("viewer3d.style.stick")}</option><option value="sphere">{t("viewer3d.style.sphere")}</option></select></label>;
}
