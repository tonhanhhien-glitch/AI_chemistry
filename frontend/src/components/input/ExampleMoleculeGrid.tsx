import { useI18n } from "../../i18n";
import { geometryLabel } from "../../utils/geometryLabels";
import type { MoleculeSummary } from "../../types/molecule";

export default function ExampleMoleculeGrid({ examples, onSelect }: { examples: MoleculeSummary[]; onSelect: (example: MoleculeSummary) => void }) {
  const { t } = useI18n();
  return <div className="example-grid">{examples.map((item) => <button className="example-chip" key={item.id} onClick={() => onSelect(item)}><strong>{item.formula}</strong><span>{item.name_vi}</span><small>{item.ax_en} · {geometryLabel(t, item.molecular_geometry)}</small></button>)}</div>;
}
