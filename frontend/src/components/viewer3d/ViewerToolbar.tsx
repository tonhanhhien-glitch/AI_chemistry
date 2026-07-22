import { useI18n } from "../../i18n";
import AtomLabelToggle from "./AtomLabelToggle";
import StyleSelector, { type ViewerStyle } from "./StyleSelector";

export default function ViewerToolbar({ style, labels, onStyle, onLabels, onReset, onFullscreen }: { style: ViewerStyle; labels: boolean; onStyle: (value: ViewerStyle) => void; onLabels: (value: boolean) => void; onReset: () => void; onFullscreen: () => void }) {
  const { t } = useI18n();
  return <div className="viewer-toolbar"><StyleSelector value={style} onChange={onStyle} /><AtomLabelToggle checked={labels} onChange={onLabels} /><button className="secondary-button" onClick={onReset}>{t("viewer3d.reset")}</button><button className="secondary-button" onClick={onFullscreen}>{t("viewer3d.fullscreen")}</button></div>;
}
