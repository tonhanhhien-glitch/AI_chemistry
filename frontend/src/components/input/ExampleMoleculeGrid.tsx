import type { MoleculeSummary } from "../../types/molecule";

export default function ExampleMoleculeGrid({ examples, onSelect }: { examples: MoleculeSummary[]; onSelect: (example: MoleculeSummary) => void }) {
  return <div className="example-grid">{examples.map((item) => <button className="example-chip" key={item.id} onClick={() => onSelect(item)}><strong>{item.formula}</strong><span>{item.name_vi}</span><small>{item.ax_en} · {item.molecular_geometry_vi}</small></button>)}</div>;
}
