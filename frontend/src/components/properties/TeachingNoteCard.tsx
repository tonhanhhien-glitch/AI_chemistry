import { useI18n } from "../../i18n";

export default function TeachingNoteCard({ note }: { note: string }) {
  const { t } = useI18n();
  return <aside className="teaching-note"><span aria-hidden="true">✦</span><div><strong>{t("teachingNote.title")}</strong><p>{note}</p></div></aside>;
}
