import { NavLink } from "react-router-dom";

import { useI18n } from "../../i18n";
import LanguageToggle from "./LanguageToggle";

const links: Array<[string, string]> = [
  ["/", "nav.home"],
  ["/analysis", "nav.analysis"],
  ["/examples", "nav.examples"],
  ["/rules", "nav.rules"],
  ["/survey", "nav.survey"],
];

export default function Header() {
  const { t } = useI18n();
  return <header className="site-header"><NavLink className="brand" to="/">VSEPR<span>Lab</span></NavLink><nav aria-label={t("nav.ariaMain")}>{links.map(([to, label]) => <NavLink key={to} to={to} className={({ isActive }) => isActive ? "active" : ""}>{t(label)}</NavLink>)}</nav><LanguageToggle /></header>;
}
