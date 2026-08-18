import { useI18n } from "../../i18n";
import { ChemFormula } from "../../utils/chemFormula";
import { geometryLabel } from "../../utils/geometryLabels";
import type { AnalysisResult } from "../../types/analysis";

export default function PipelineSummary({ result }: { result: AnalysisResult }) {
  const { lang, t } = useI18n();
  const name = lang === "vi" ? result.molecule.name_vi || result.molecule.name_en : result.molecule.name_en || result.molecule.name_vi;
  const preferredList = result.bond_angles.preferred || [];
  const distinctLabels = Array.from(new Set(preferredList.map((item) => item.display_label)));
  const angleSummary = distinctLabels.length > 0
    ? distinctLabels.join(" / ")
    : result.vsepr.ideal_angle;

  return (
    <div className="pipeline-summary">
      <div>
        <span>{t("workflow.summary.substance")}</span>
        <strong><ChemFormula text={result.molecule.formula} /></strong>
        <small>{name}</small>
      </div>
      <div>
        <span>{t("workflow.summary.classification")}</span>
        <strong><ChemFormula text={result.vsepr.ax_en} /></strong>
        <small>
          {result.vsepr.bonding_domains} {t("workflow.summary.bonds")} · {result.vsepr.lone_pair_domains} {t("workflow.summary.lonePairs")}
        </small>
      </div>
      <div>
        <span>{t("workflow.summary.geometry")}</span>
        <strong>{geometryLabel(t, result.vsepr.molecular_geometry)}</strong>
        <small>{angleSummary}</small>
      </div>
    </div>
  );
}
