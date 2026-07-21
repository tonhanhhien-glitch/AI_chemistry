import GeometryIcon from "./GeometryIcon";

export default function GeometryCard({ title, geometry, geometryVi, angle }: { title: string; geometry: string; geometryVi: string; angle?: string }) {
  return <article className="geometry-card"><GeometryIcon geometry={geometry} label={geometryVi} /><div><span>{title}</span><strong>{geometryVi}</strong><small>{geometry}{angle ? ` · ${angle}` : ""}</small></div></article>;
}
