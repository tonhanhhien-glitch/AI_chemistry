import { useI18n } from "../../i18n";
import type { BondAnglesResult } from "../../types/bondAngles";

export default function BondAngleEvidenceCard({ angles, notation }: { angles: BondAnglesResult; notation?: string }) {
  const { t } = useI18n();
  const preferred = angles.preferred[0];
  const prediction = angles.vsepr_prediction[0];
  if (!preferred && !prediction) return null;

  const pattern = preferred ? `${preferred.atom1_element}–${preferred.center_element}–${preferred.atom2_element}` : "";
  const evidenceLabel = preferred?.is_experimental
    ? t("angles.experimental")
    : preferred?.is_computed
      ? t("angles.computed")
      : preferred?.evidence_type === "curated_reference"
        ? t("angles.curated")
        : t("angles.illustrative");
  const phaseLabel = preferred?.phase === "gas" ? t("angles.phase.gas") : preferred?.phase;
  const preferredTitle = preferred?.evidence_type === "ideal_vsepr"
    ? t("angles.vseprEstimate")
    : t("angles.moleculeSpecific");
  const preferredSource = preferred?.evidence_type === "ideal_vsepr"
    ? t("angles.idealModel")
    : preferred?.source_name;
  const showPrediction = Boolean(prediction && preferred?.id !== prediction.id);

  return <section className="bond-angle-evidence" aria-label={t("angles.cardAria")}>
    {preferred && <div>
      <span>{preferredTitle}</span>
      <strong>{pattern}: {preferred.display_label}</strong>
      <small>{evidenceLabel}{phaseLabel ? ` · ${phaseLabel}` : ""} · {preferred.source_url
        ? <a href={preferred.source_url} target="_blank" rel="noreferrer">{preferred.source_name}</a>
        : preferredSource}</small>
      {preferred.is_computed && <em>{t("angles.notExperimental")}</em>}
    </div>}
    {showPrediction && prediction && <div>
      <span>{t("angles.vseprPrediction")}</span>
      <strong>{notation && <>{notation}: </>}{prediction.display_label}</strong>
      <small>{t("angles.generalModel")}</small>
    </div>}
  </section>;
}
