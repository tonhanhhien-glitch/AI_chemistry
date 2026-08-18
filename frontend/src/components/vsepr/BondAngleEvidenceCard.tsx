import { useI18n } from "../../i18n";
import type { BondAnglesResult } from "../../types/bondAngles";

/**
 * Shows every molecule-specific preferred bond angle, not just the first.
 *
 * A T-shaped or seesaw geometry has several inequivalent angles, so the card lists each
 * one with how many symmetry-equivalent copies it stands for.
 */
export default function BondAngleEvidenceCard({ angles }: { angles: BondAnglesResult; notation?: string }) {
  const { t } = useI18n();
  const specific = (angles.preferred || []).filter((item) => item.evidence_type !== "ideal_vsepr");
  if (!specific.length) return null;

  return (
    <section className="bond-angle-evidence" aria-label={t("angles.cardAria")}>
      {specific.map((item) => {
        const pattern = `${item.atom1_element}–${item.center_element}–${item.atom2_element}`;
        const evidenceLabel = item.is_experimental
          ? t("angles.experimental")
          : item.is_computed
            ? t("angles.computed")
            : item.evidence_type === "curated_reference"
              ? t("angles.curated")
              : t("angles.illustrative");
        const phaseLabel = item.phase === "gas" ? t("angles.phase.gas") : item.phase;
        const title = t("angles.moleculeSpecific");
        const source = item.source_name;
        const multiplicity = item.equivalent_count > 1 ? ` · ×${item.equivalent_count}` : "";
        return (
          <div key={item.id}>
            <span>{title}{multiplicity}</span>
            <strong>{pattern}: {item.display_label}</strong>
            <small>
              {evidenceLabel}
              {phaseLabel ? ` · ${phaseLabel}` : ""}
              {" · "}
              {item.source_url ? (
                <a href={item.source_url} target="_blank" rel="noreferrer">
                  {item.source_name}
                </a>
              ) : (
                source
              )}
              {item.reference ? ` · ${item.reference}` : ""}
            </small>
            {item.is_computed && <em>{t("angles.notExperimental")}</em>}
          </div>
        );
      })}
    </section>
  );
}
