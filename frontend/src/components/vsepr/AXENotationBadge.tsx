import { useI18n } from "../../i18n";
import { formatChemFormula } from "../../utils/chemFormula";

export default function AXENotationBadge({ notation }: { notation: string }) {
  const { t } = useI18n();
  return <span className="ax-badge chemical-formula" aria-label={t("vsepr.badgeAria", { notation })}>{formatChemFormula(notation)}</span>;
}
