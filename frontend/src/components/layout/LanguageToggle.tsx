import { useI18n } from "../../i18n";

// Switches the UI between Vietnamese and English. Label shows the language it
// will switch to, so it reads "English" while in Vietnamese and vice versa.
export default function LanguageToggle() {
  const { lang, setLang, t } = useI18n();
  return (
    <button
      type="button"
      className="lang-toggle"
      aria-label={t("lang.toggleAria")}
      onClick={() => setLang(lang === "vi" ? "en" : "vi")}
    >
      {t("lang.switchTo")}
    </button>
  );
}
