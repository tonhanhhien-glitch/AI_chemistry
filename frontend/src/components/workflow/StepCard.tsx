import type { ReactNode } from "react";

export default function StepCard({ number, title, children, className = "" }: { number?: number; title: string; children: ReactNode; className?: string }) {
  return <section className={`learning-card ${className}`}><header className="card-heading"><h2>{title}</h2></header>{children}</section>;
}
