import { useState } from "react";
import { useI18n } from "../../i18n";
import { useMoleculeSearch } from "../../hooks/useMoleculeSearch";
import type { MoleculeSummary } from "../../types/molecule";

export default function MoleculeSearchBox({ onSelect }: { onSelect: (item: MoleculeSummary) => void }) {
  const { t } = useI18n();
  const [query, setQuery] = useState(""); const results = useMoleculeSearch(query);
  return <div className="molecule-search"><label htmlFor="molecule-search">{t("moleculeSearch.label")}</label><input id="molecule-search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder={t("moleculeSearch.placeholder")} />{results.length > 0 && <ul>{results.map((item) => <li key={item.id}><button onClick={() => onSelect(item)}>{item.formula} — {item.name_vi}</button></li>)}</ul>}</div>;
}
