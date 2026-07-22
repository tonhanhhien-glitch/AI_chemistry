import { useI18n } from "../../i18n";

export default function Footer() {
  const { t } = useI18n();
  return <footer className="site-footer"><p><strong>VSEPRLab</strong> · {t("footer.tagline")}</p><p>{t("footer.note")}</p></footer>;
}
