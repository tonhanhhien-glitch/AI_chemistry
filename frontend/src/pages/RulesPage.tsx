import { useEffect, useState } from "react";
import { getExamples, getVseprRules, type VseprRuleRecord } from "../api/moleculeApi";
import PageContainer from "../components/layout/PageContainer";
import GeometryIcon from "../components/vsepr/GeometryIcon";
import { useI18n } from "../i18n";
import { geometryLabel } from "../utils/geometryLabels";
import type { MoleculeSummary } from "../types/molecule";

export default function RulesPage() {
  const { t } = useI18n();
  const [rules, setRules] = useState<VseprRuleRecord[]>([]); const [examples, setExamples] = useState<MoleculeSummary[]>([]); const [error, setError] = useState("");
  useEffect(() => { void Promise.all([getVseprRules(), getExamples()]).then(([ruleRows, exampleRows]) => { setRules(ruleRows); setExamples(exampleRows); }).catch(() => setError(t("rules.loadError"))); }, [t]);
  return <PageContainer><header className="page-intro"><p className="eyebrow">{t("rules.eyebrow")}</p><h1>{t("rules.title")}</h1><p>{t("rules.intro")}</p></header>{error && <p className="error-message">{error}</p>}<div className="rules-grid">{rules.map((rule) => <article className="rule-card" key={rule.ax_en}><GeometryIcon geometry={rule.molecular_geometry} label={geometryLabel(t, rule.molecular_geometry)} /><div><strong>{rule.ax_en}</strong><p>{rule.bonding_domains} {t("rules.bondingDomains")} · {rule.lone_pair_domains} {t("rules.lonePairs")}</p><dl><dt>{t("rules.electronDomain")}</dt><dd>{geometryLabel(t, rule.electron_geometry)}</dd><dt>{t("rules.molecular")}</dt><dd>{geometryLabel(t, rule.molecular_geometry)}</dd><dt>{t("rules.angle")}</dt><dd>{rule.ideal_angle}</dd><dt>{t("rules.example")}</dt><dd>{examples.filter((item) => item.ax_en === rule.ax_en).map((item) => item.formula).join(", ") || "—"}</dd></dl><small>{t(`rules.teachingNote.${rule.ax_en}`)}</small></div></article>)}</div><p className="offline-notice">{t("rules.footnote")}</p></PageContainer>;
}
