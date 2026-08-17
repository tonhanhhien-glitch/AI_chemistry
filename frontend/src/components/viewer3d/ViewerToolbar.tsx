import { useI18n } from "../../i18n";
import type { ViewerStyle } from "./StyleSelector";

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

  return (
    <div className="viewer-controls-overlay">
      <div className="viewer-controls-left">
        <div className="viewer-glass-panel">
          <label className="viewer-style-control" title={t("viewer3d.styleLabel")}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <circle cx="12" cy="12" r="3" />
              <circle cx="19" cy="5" r="2" />
              <circle cx="5" cy="19" r="2" />
              <path d="M10 10l-3.5 7" />
              <path d="M14 14l3.5-7" />
            </svg>
            <select
              aria-label={t("viewer3d.styleLabel")}
              value={props.style}
              onChange={(event) => props.onStyle(event.target.value as ViewerStyle)}
            >
              <option value="stick">{t("viewer3d.style.stick")}</option>
              <option value="ball-and-stick">{t("viewer3d.style.ballStick")}</option>
              <option value="space-filling">{t("viewer3d.style.sphere")}</option>
            </select>
          </label>
        </div>
      </div>

      <div className="viewer-controls-right">
        <div className="viewer-glass-panel">
          <label className={`viewer-toggle-btn ${props.labels ? "active" : ""}`} title={t("viewer3d.atomLabels")}>
            <input
              type="checkbox"
              checked={props.labels}
              onChange={(event) => props.onLabels(event.target.checked)}
            />
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M4 19L9.5 5h1L16 19" />
              <path d="M6.5 14h7" />
              <path d="M18 11v8" />
              <path d="M18 15a3 3 0 1 1 0-6" />
            </svg>
            <span className="viewer-toggle-label">{t("viewer3d.atomLabels")}</span>
          </label>

          <label className={`viewer-toggle-btn ${props.angles ? "active" : ""} ${!props.hasAngles ? "disabled" : ""}`} title={t("viewer3d.angles")}>
            <input
              type="checkbox"
              checked={props.angles}
              disabled={!props.hasAngles}
              onChange={(event) => props.onAngles(event.target.checked)}
            />
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M3 21h18" />
              <path d="M3 21L17 5" />
              <path d="M9 21a6 6 0 0 0-6-6" />
            </svg>
            <span className="viewer-toggle-label">{t("viewer3d.angles")}</span>
          </label>

          <label className={`viewer-toggle-btn ${props.lonePairs ? "active" : ""} ${!props.hasLonePairs ? "disabled" : ""}`} title={t("viewer3d.lonePairs")}>
            <input
              type="checkbox"
              checked={props.lonePairs}
              disabled={!props.hasLonePairs}
              onChange={(event) => props.onLonePairs(event.target.checked)}
            />
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <ellipse cx="12" cy="12" rx="5" ry="8" transform="rotate(30 12 12)" strokeDasharray="3 2" />
              <circle cx="10" cy="10" r="1.5" fill="currentColor" stroke="none" />
              <circle cx="14" cy="14" r="1.5" fill="currentColor" stroke="none" />
            </svg>
            <span className="viewer-toggle-label">{t("viewer3d.lonePairs")}</span>
          </label>

          <span className="viewer-control-divider" aria-hidden="true" />

          <button
            type="button"
            className="viewer-icon-btn"
            disabled={!props.hasAngles}
            onClick={props.onViewAngle}
            title={t("viewer3d.viewAngle")}
            aria-label={t("viewer3d.viewAngle")}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <circle cx="12" cy="12" r="3" />
              <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
            </svg>
          </button>

          <button
            type="button"
            className="viewer-icon-btn"
            onClick={props.onReset}
            title={t("viewer3d.reset")}
            aria-label={t("viewer3d.reset")}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
              <path d="M3 3v5h5" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
