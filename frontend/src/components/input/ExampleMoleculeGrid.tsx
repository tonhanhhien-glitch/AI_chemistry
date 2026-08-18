import { useI18n } from "../../i18n";
import { ChemFormula } from "../../utils/chemFormula";
import { geometryLabel } from "../../utils/geometryLabels";
import type { MoleculeSummary } from "../../types/molecule";

export default function ExampleMoleculeGrid({ examples, onSelect }: { examples: MoleculeSummary[]; onSelect: (example: MoleculeSummary) => void }) {
  const { lang, t } = useI18n();
  return (
    <div className="example-grid">
      {examples.map((item) => {
        const name = lang === "vi" ? item.name_vi || item.name_en : item.name_en || item.name_vi;
        return (
          <button className="example-chip" key={item.id} onClick={() => onSelect(item)}>
            <strong><ChemFormula text={item.formula} /></strong>
            <span>{name}</span>
            <small><ChemFormula text={item.ax_en} /> · {geometryLabel(t, item.molecular_geometry)}</small>
          </button>
        );
      })}
    </div>
  );
}
