import type { ReactNode } from "react";
import { useI18n } from "../../i18n";

// A flanking pane in the analysis workspace. When open it shows a titled body;
// when collapsed it shrinks to a vertical rail with a button to reopen it, so
// the central 3D model can claim the extra width.
export default function WorkspacePane({ side, title, open, onToggle, children }: { side: "left" | "right"; title: string; open: boolean; onToggle: (open: boolean) => void; children: ReactNode }) {
  const { t } = useI18n();
  if (!open) {
    return (
      <aside className={`workspace-pane pane-${side} is-collapsed`} aria-label={title}>
        <button type="button" className="pane-rail" onClick={() => onToggle(true)} aria-label={t("analysis.pane.expand", { title })} title={t("analysis.pane.expand", { title })}>
          <span className="pane-rail-chevron" aria-hidden="true">{side === "left" ? "›" : "‹"}</span>
          <span className="pane-rail-label">{title}</span>
        </button>
      </aside>
    );
  }
  return (
    <aside className={`workspace-pane pane-${side}`} aria-label={title}>
      <div className="pane-head">
        <p className="pane-title">{title}</p>
        <button type="button" className="pane-toggle" onClick={() => onToggle(false)} aria-label={t("analysis.pane.collapse", { title })} title={t("analysis.pane.collapse", { title })}>{side === "left" ? "‹" : "›"}</button>
      </div>
      <div className="pane-body">{children}</div>
    </aside>
  );
}
