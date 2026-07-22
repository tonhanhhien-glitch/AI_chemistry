import { useI18n } from "../../i18n";
import type { VseprResult } from "../../types/vsepr";

export default function ElectronDomainTable({ result }: { result: VseprResult }) {
  const { t } = useI18n();
  return <div className="domain-grid"><div><span>{t("vsepr.domain.bonding")}</span><strong>{result.bonding_domains}</strong></div><div><span>{t("vsepr.domain.lonePairs")}</span><strong>{result.lone_pair_domains}</strong></div><div><span>{t("vsepr.domain.steric")}</span><strong>{result.steric_number}</strong></div></div>;
}
