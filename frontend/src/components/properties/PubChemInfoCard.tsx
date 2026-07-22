import { useI18n } from "../../i18n";
import type { Molecule } from "../../types/molecule";

export default function PubChemInfoCard({ molecule }: { molecule: Molecule }) {
  const { t } = useI18n();
  return <aside className="reference-card"><h3>{t("pubchem.title")}</h3>{molecule.pubchem_cid ? <p>PubChem CID: {molecule.pubchem_cid}</p> : <p>{t("pubchem.noCid")}</p>}{molecule.smiles && <p><code>{molecule.smiles}</code></p>}</aside>;
}
