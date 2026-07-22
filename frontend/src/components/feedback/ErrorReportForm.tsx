import { useI18n } from "../../i18n";
import FeedbackForm from "./FeedbackForm";

export default function ErrorReportForm({ moleculeId }: { moleculeId: string }) {
  const { t } = useI18n();
  return <details><summary>{t("feedback.errorReport.summary")}</summary><p>{t("feedback.errorReport.body")}</p><FeedbackForm moleculeId={moleculeId} /></details>;
}
