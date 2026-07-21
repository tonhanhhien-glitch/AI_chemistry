import AtomLabelToggle from "./AtomLabelToggle";
import StyleSelector, { type ViewerStyle } from "./StyleSelector";

export default function ViewerToolbar({ style, labels, onStyle, onLabels, onReset, onFullscreen }: { style: ViewerStyle; labels: boolean; onStyle: (value: ViewerStyle) => void; onLabels: (value: boolean) => void; onReset: () => void; onFullscreen: () => void }) {
  return <div className="viewer-toolbar"><StyleSelector value={style} onChange={onStyle} /><AtomLabelToggle checked={labels} onChange={onLabels} /><button className="secondary-button" onClick={onReset}>Đặt lại</button><button className="secondary-button" onClick={onFullscreen}>Toàn màn hình</button></div>;
}
