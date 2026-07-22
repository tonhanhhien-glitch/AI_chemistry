import { useI18n } from "../../i18n";
import type { LewisStructure } from "../../types/lewis";

export default function FormalChargeTable({ structure }: { structure: LewisStructure }) {
  const { t } = useI18n();
  return <table className="compact-table"><caption>{t("lewis.formalCharge.caption")}</caption><thead><tr><th>{t("lewis.formalCharge.atom")}</th><th>{t("lewis.formalCharge.lonePairs")}</th><th>{t("lewis.formalCharge.charge")}</th></tr></thead><tbody>{structure.atoms.map((atom) => <tr key={atom.id}><td>{atom.element} <small>({atom.id})</small></td><td>{atom.lone_pairs}</td><td>{atom.formal_charge > 0 ? `+${atom.formal_charge}` : atom.formal_charge}</td></tr>)}</tbody></table>;
}
