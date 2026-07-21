import type { ReactNode } from "react";

export default function Sidebar({ title, children }: { title: string; children: ReactNode }) {
  return <aside className="sidebar" aria-label={title}><h2>{title}</h2>{children}</aside>;
}
