import { useI18n } from "../../i18n";
import type { Structure3D } from "../../types/structure3d";

/**
 * States plainly where the drawn coordinates came from.
 *
 * A student must be able to tell an experimental measurement from a computed conformer
 * and from an educational idealization at a glance, so the badge names the evidence
 * type, the source and — for measurements — the reference and phase. Vague wording such
 * as "real angle" is deliberately avoided for anything that is not a measurement.
 */
export default function GeometryProvenanceBadge({ structure }: { structure: Structure3D }) {
  const { t, lang } = useI18n();
  const evidence = structure.geometry_evidence;
  const provenance = evidence
    ? (lang === "en" ? evidence.provenance_label_en : evidence.provenance_label_vi)
    : structure.source_label;
  const tone = structure.is_experimental ? "experimental" : structure.is_computed ? "computed" : "illustrative";

  return <div className={`geometry-provenance geometry-provenance-${tone}`} aria-label={t("viewer3d.provenanceAria")}>
    <strong>{provenance}</strong>
    <span>{structure.source_label}</span>
    {evidence && <small>
      {evidence.source_reference && <span className="provenance-reference">{evidence.source_reference}</span>}
      {evidence.phase && <span>{evidence.phase}</span>}
      {evidence.point_group && <span>{t("viewer3d.pointGroup")}: {evidence.point_group}</span>}
      {evidence.source_url && <a href={evidence.source_url} target="_blank" rel="noreferrer">{evidence.source_name}</a>}
    </small>}
    {structure.is_computed && <em>{t("viewer3d.computedNotice")}</em>}
    {structure.is_illustrative && <em>{t("viewer3d.idealNotice")}</em>}
    {evidence?.coordinates_are_fitted && <em>{t("viewer3d.fittedNotice")}</em>}
  </div>;
}
