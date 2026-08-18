import { useState } from "react";
import { useI18n } from "../../i18n";
import { useMoleculeSearch } from "../../hooks/useMoleculeSearch";
import { ChemFormula } from "../../utils/chemFormula";
import { geometryLabel } from "../../utils/geometryLabels";
import type { MoleculeSummary } from "../../types/molecule";

export default function MoleculeSearchBox({ onSelect }: { onSelect: (item: MoleculeSummary) => void }) {
  const { lang, t } = useI18n();
  const [query, setQuery] = useState("");
  const { results } = useMoleculeSearch(query);
  return (
    <div className="molecule-search">
      <label htmlFor="molecule-search">{t("moleculeSearch.label")}</label>
      <input
        id="molecule-search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder={t("moleculeSearch.placeholder")}
      />
      {results.length > 0 && (
        <ul>
          {results.map((item) => {
            const name = lang === "vi" ? item.name_vi || item.name_en : item.name_en || item.name_vi;
            const shape = geometryLabel(t, item.molecular_geometry);
            return (
              <li key={item.id}>
                <button onClick={() => onSelect(item)}>
                  <ChemFormula text={item.formula} /> — {name} {shape && `(${shape})`}
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
