import { useI18n } from "../../i18n";
import type { PropertyItem } from "../../types/molecule";

// Maps a property's `provenance` value to its translation key.
const sourceLabelKeys: Record<string, string> = { curated: "property.source.curated", computed: "property.source.computed", "PubChem reference": "property.source.pubchem" };

export default function PropertyTable({ properties }: { properties: PropertyItem[] }) {
  const { t } = useI18n();
  return <div className="property-groups">{Object.entries(sourceLabelKeys).map(([source, labelKey]) => { const rows = properties.filter((item) => item.provenance === source); if (!rows.length) return null; return <section key={source}><h3>{t(labelKey)}</h3><table><tbody>{rows.map((item) => <tr key={item.key}><th>{item.label_vi}</th><td>{item.value}{item.unit ? ` ${item.unit}` : ""}{item.note_vi && <small>{item.note_vi}</small>}</td></tr>)}</tbody></table></section>; })}</div>;
}
