import type { PropertyItem } from "../../types/molecule";

const labels = { curated: "Dữ liệu tuyển chọn", computed: "Giá trị tính toán", "PubChem reference": "Tham chiếu PubChem" };

export default function PropertyTable({ properties }: { properties: PropertyItem[] }) {
  return <div className="property-groups">{Object.entries(labels).map(([source, label]) => { const rows = properties.filter((item) => item.provenance === source); if (!rows.length) return null; return <section key={source}><h3>{label}</h3><table><tbody>{rows.map((item) => <tr key={item.key}><th>{item.label_vi}</th><td>{item.value}{item.unit ? ` ${item.unit}` : ""}{item.note_vi && <small>{item.note_vi}</small>}</td></tr>)}</tbody></table></section>; })}</div>;
}
