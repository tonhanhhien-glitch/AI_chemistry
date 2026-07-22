import { useI18n } from "../../i18n";
import { geometryLabel } from "../../utils/geometryLabels";
import type { AnalysisResult } from "../../types/analysis";

export default function PipelineSummary({ result }: { result: AnalysisResult }) {
  const { t } = useI18n();
  return <div className="pipeline-summary"><div><span>{t("workflow.summary.substance")}</span><strong>{result.molecule.formula}</strong><small>{result.molecule.name_vi}</small></div><div><span>{t("workflow.summary.classification")}</span><strong>{result.vsepr.ax_en}</strong><small>{result.vsepr.bonding_domains} {t("workflow.summary.bonds")} · {result.vsepr.lone_pair_domains} {t("workflow.summary.lonePairs")}</small></div><div><span>{t("workflow.summary.geometry")}</span><strong>{geometryLabel(t, result.vsepr.molecular_geometry)}</strong><small>{result.vsepr.ideal_angle}</small></div></div>;
}
