import type { LewisStructure } from "../../types/lewis";

export default function FormalChargeTable({ structure }: { structure: LewisStructure }) {
  return <table className="compact-table"><caption>Điện tích hình thức theo nguyên tử</caption><thead><tr><th>Nguyên tử</th><th>Cặp e tự do</th><th>Điện tích</th></tr></thead><tbody>{structure.atoms.map((atom) => <tr key={atom.id}><td>{atom.element} <small>({atom.id})</small></td><td>{atom.lone_pairs}</td><td>{atom.formal_charge > 0 ? `+${atom.formal_charge}` : atom.formal_charge}</td></tr>)}</tbody></table>;
}
