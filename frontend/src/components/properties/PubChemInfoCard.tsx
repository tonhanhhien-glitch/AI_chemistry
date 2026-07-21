import type { Molecule } from "../../types/molecule";

export default function PubChemInfoCard({ molecule }: { molecule: Molecule }) {
  return <aside className="reference-card"><h3>Tham chiếu cấu trúc</h3>{molecule.pubchem_cid ? <p>PubChem CID: {molecule.pubchem_cid}</p> : <p>Chưa gắn CID vì chưa hoàn tất xác minh nguồn. Không có dữ liệu giả được hiển thị.</p>}{molecule.smiles && <p><code>{molecule.smiles}</code></p>}</aside>;
}
