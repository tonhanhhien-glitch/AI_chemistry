import { useI18n } from "../../i18n";

export default function ViewerFallback({ message }: { message?: string }) {
  const { t } = useI18n();
  return <div className="viewer-fallback" role="status"><span aria-hidden="true">◌</span><p>{message ?? t("viewer3d.fallback")}</p></div>;
}
