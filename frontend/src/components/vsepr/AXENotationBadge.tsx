import { useI18n } from "../../i18n";

export default function AXENotationBadge({ notation }: { notation: string }) {
  const { t } = useI18n();
  return <span className="ax-badge" aria-label={t("vsepr.badgeAria", { notation })}>{notation}</span>;
}
