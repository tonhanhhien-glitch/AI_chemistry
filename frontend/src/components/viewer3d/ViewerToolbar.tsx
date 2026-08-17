import { useI18n } from "../../i18n";
import AtomLabelToggle from "./AtomLabelToggle";
import StyleSelector, { type ViewerStyle } from "./StyleSelector";

interface ViewerToolbarProps {
  style: ViewerStyle;
  labels: boolean;
  angles: boolean;
  lonePairs: boolean;
  hasAngles: boolean;
  hasLonePairs: boolean;
  onStyle: (value: ViewerStyle) => void;
  onLabels: (value: boolean) => void;
  onAngles: (value: boolean) => void;
  onLonePairs: (value: boolean) => void;
  onViewAngle?: () => void;
  onReset?: () => void;
}

export default function ViewerToolbar(props: ViewerToolbarProps) {
  const { t } = useI18n();
  return <div className="viewer-toolbar">
    <div className="viewer-toolbar-main">
      <StyleSelector value={props.style} onChange={props.onStyle} />
      <button type="button" className="secondary-button" disabled={!props.hasAngles} onClick={props.onViewAngle}>{t("viewer3d.viewAngle")}</button>
      <button type="button" className="secondary-button" onClick={props.onReset}>{t("viewer3d.reset")}</button>
    </div>
    <div className="viewer-toolbar-toggles">
      <AtomLabelToggle checked={props.labels} onChange={props.onLabels} />
      <label className="check-control"><input type="checkbox" checked={props.angles} disabled={!props.hasAngles} onChange={(event) => props.onAngles(event.target.checked)} />{t("viewer3d.angles")}</label>
      <label className="check-control"><input type="checkbox" checked={props.lonePairs} disabled={!props.hasLonePairs} onChange={(event) => props.onLonePairs(event.target.checked)} />{t("viewer3d.lonePairs")}</label>
    </div>
  </div>;
}
