import { useI18n } from "../../i18n";
import { geometryLabel } from "../../utils/geometryLabels";
import type { VseprResult } from "../../types/vsepr";
import AXENotationBadge from "./AXENotationBadge";
import ElectronDomainTable from "./ElectronDomainTable";
import GeometryCard from "./GeometryCard";

export default function VSEPRCard({ result }: { result: VseprResult }) {
  const { t, lang } = useI18n();
  const en = lang === "en";
  const teachingNote = en ? result.teaching_note_en : result.teaching_note_vi;
  const distortionNote = en ? result.distortion_note_en : result.distortion_note_vi;
  const hybridizationWarning = en ? result.hybridization_warning_en : result.hybridization_warning_vi;
  return <div className="vsepr-card"><div className="notation-row"><AXENotationBadge notation={result.ax_en} /><p>{t("vsepr.notationHint")}</p></div><ElectronDomainTable result={result} /><div className="geometry-grid"><GeometryCard title={t("vsepr.electronGeometry")} geometry={result.electron_geometry} geometryVi={geometryLabel(t, result.electron_geometry)} /><GeometryCard title={t("vsepr.molecularGeometry")} geometry={result.molecular_geometry} geometryVi={geometryLabel(t, result.molecular_geometry)} angle={`${t("vsepr.referenceAngle")}: ${result.ideal_angle}`} /></div>{distortionNote && <p className="callout">{distortionNote}</p>}<p>{teachingNote}</p>{result.pedagogical_hybridization && <p className="muted">{t("vsepr.pedagogicalLabel")} <strong>{result.pedagogical_hybridization}</strong>. {hybridizationWarning}</p>}</div>;
}
