import { useState, type ReactNode } from "react";

// One accordion row inside the analysis info pane. The header is a real heading
// wrapping a button, following the WAI-ARIA accordion pattern.
export default function CollapsibleSection({ number, title, defaultOpen = true, children }: { number?: number; title: string; defaultOpen?: boolean; children: ReactNode }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section className="accordion-section">
      <h2 className="accordion-header">
        <button type="button" className="accordion-trigger" aria-expanded={open} onClick={() => setOpen((value) => !value)}>
          <span className="accordion-title">{title}</span>
          <span className="accordion-chevron" aria-hidden="true">{open ? "▾" : "▸"}</span>
        </button>
      </h2>
      {open && <div className="accordion-panel">{children}</div>}
    </section>
  );
}
