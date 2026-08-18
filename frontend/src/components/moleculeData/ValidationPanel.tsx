import { useI18n } from "../../i18n";
import type { ValidationIssue, ValidationReport } from "../../types/moleculeAdmin";

function IssueList({ issues, lang }: { issues: ValidationIssue[]; lang: "vi" | "en" }) {
  return (
    <ul>
      {issues.map((issue, index) => (
        <li key={index}>
          {issue.field && <strong>{issue.field}: </strong>}
          {lang === "vi" ? issue.message_vi : issue.message_en}
        </li>
      ))}
    </ul>
  );
}

export default function ValidationPanel({ report }: { report: ValidationReport | null }) {
  const { t, lang } = useI18n();
  if (!report) return null;
  return (
    <div className={report.is_valid ? "molecule-data-validation valid" : "molecule-data-validation invalid"}>
      <p>
        <strong>{report.is_valid ? t("moleculeData.validation.valid") : t("moleculeData.validation.invalid")}</strong>
      </p>
      {report.errors.length > 0 && (
        <div>
          <h4>{t("moleculeData.validation.errors")}</h4>
          <IssueList issues={report.errors} lang={lang} />
        </div>
      )}
      {report.warnings.length > 0 && (
        <div>
          <h4>{t("moleculeData.validation.warnings")}</h4>
          <IssueList issues={report.warnings} lang={lang} />
        </div>
      )}
      {report.info.length > 0 && (
        <div>
          <h4>{t("moleculeData.validation.info")}</h4>
          <IssueList issues={report.info} lang={lang} />
        </div>
      )}
    </div>
  );
}
