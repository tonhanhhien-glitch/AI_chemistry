import { useI18n } from "../../i18n";

export default function ResonanceNote({ forms, note }: { forms: number; note: string | null }) {
  const { t } = useI18n();
  if (forms <= 1 && !note) return null;
  return <aside className="callout"><strong>↔ {t("lewis.resonance.forms", { forms })}</strong><p>{note}</p></aside>;
}
