import { useI18n } from "../../i18n";
import { ChemFormula } from "../../utils/chemFormula";
import { geometryLabel } from "../../utils/geometryLabels";
import type { AnalysisResult } from "../../types/analysis";
export default function PipelineSummary({ result }: { result: AnalysisResult }) {
  const { t } = useI18n(); const name = result.molecule.name_en; const preferred = result.bond_angles.preferred[0];
  return <div className="pipeline-summary"><div><span>{t("workflow.summary.substance")}</span><strong><ChemFormula text={result.molecule.formula} /></strong><small>{name}</small></div><div><span>{t("workflow.summary.classification")}</span><strong><ChemFormula text={result.vsepr.ax_en} /></strong><small>{result.vsepr.bonding_domains} {t("workflow.summary.bonds")} · {result.vsepr.lone_pair_domains} {t("workflow.summary.lonePairs")}</small></div><div><span>{t("workflow.summary.geometry")}</span><strong>{geometryLabel(t, result.vsepr.molecular_geometry)}</strong><small>{preferred ? `${preferred.atom1_element}–${preferred.center_element}–${preferred.atom2_element}: ${preferred.display_label}` : result.vsepr.ideal_angle}</small></div></div>;
}
