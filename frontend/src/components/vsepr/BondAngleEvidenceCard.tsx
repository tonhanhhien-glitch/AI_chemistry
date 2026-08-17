import { useI18n } from "../../i18n";
import { ChemFormula } from "../../utils/chemFormula";
import type { BondAnglesResult } from "../../types/bondAngles";

/**
 * Shows every preferred bond angle, not just the first.
 *
 * A T-shaped or seesaw geometry has several inequivalent angles, so the card lists each
 * one with how many symmetry-equivalent copies it stands for. The general AXnEm
 * prediction is kept alongside as secondary teaching information; it never replaces a
 * measured value, and a measured value is never labelled as anything vaguer than what
 * its evidence supports.
 */
export default function BondAngleEvidenceCard({ angles, notation }: { angles: BondAnglesResult; notation?: string }) {
  const { t } = useI18n();
  const preferred = angles.preferred;
  const prediction = angles.vsepr_prediction[0];
  if (!preferred.length && !prediction) return null;

  const showPrediction = Boolean(prediction && !preferred.some((item) => item.id === prediction.id));

  return <section className="bond-angle-evidence" aria-label={t("angles.cardAria")}>
    {preferred.map((item) => {
      const pattern = `${item.atom1_element}–${item.center_element}–${item.atom2_element}`;
      const evidenceLabel = item.is_experimental
        ? t("angles.experimental")
        : item.is_computed
          ? t("angles.computed")
          : item.evidence_type === "curated_reference"
            ? t("angles.curated")
            : t("angles.illustrative");
      const phaseLabel = item.phase === "gas" ? t("angles.phase.gas") : item.phase;
      const title = item.evidence_type === "ideal_vsepr" ? t("angles.vseprEstimate") : t("angles.moleculeSpecific");
      const source = item.evidence_type === "ideal_vsepr" ? t("angles.idealModel") : item.source_name;
      // A multiplicity counts real symmetry-equivalent angles in a structure. The
      // generic AXnEm estimate describes a class of molecules, so it has none to count.
      const multiplicity = item.evidence_type !== "ideal_vsepr" && item.equivalent_count > 1
        ? ` · ×${item.equivalent_count}` : "";
      return <div key={item.id}>
        <span>{title}{multiplicity}</span>
        <strong>{pattern}: {item.display_label}</strong>
        <small>{evidenceLabel}{phaseLabel ? ` · ${phaseLabel}` : ""} · {item.source_url
          ? <a href={item.source_url} target="_blank" rel="noreferrer">{item.source_name}</a>
          : source}{item.reference ? ` · ${item.reference}` : ""}</small>
        {item.is_computed && <em>{t("angles.notExperimental")}</em>}
      </div>;
    })}
    {showPrediction && prediction && <div>
      <span>{t("angles.vseprPrediction")}</span>
      <strong>{notation && <><ChemFormula text={notation} />: </>}{prediction.display_label}</strong>
      <small>{t("angles.generalModel")}</small>
    </div>}
  </section>;
}
