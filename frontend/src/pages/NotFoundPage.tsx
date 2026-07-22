import { Link } from "react-router-dom";
import PageContainer from "../components/layout/PageContainer";
import { useI18n } from "../i18n";

export default function NotFoundPage() {
  const { t } = useI18n();
  return <PageContainer><section className="not-found"><p className="eyebrow">{t("notFound.eyebrow")}</p><h1>{t("notFound.title")}</h1><p>{t("notFound.body")}</p><Link className="button button--link" to="/">{t("notFound.home")}</Link></section></PageContainer>;
}
