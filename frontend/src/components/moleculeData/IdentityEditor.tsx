import { useState } from "react";
import { parseFormula } from "../../api/formulaApi";
import { getApiErrorMessage } from "../../api/client";
import { useI18n } from "../../i18n";
import type { MoleculeDraft } from "../../types/moleculeAdmin";

function TextField({ id, label, value, onChange, required }: {
  id: string; label: string; value: string; onChange: (value: string) => void; required?: boolean;
}) {
  return (
    <div className="molecule-data-field">
      <label htmlFor={id}>{label}</label>
      <input id={id} value={value} onChange={(event) => onChange(event.target.value)} required={required} />
    </div>
  );
}

export default function IdentityEditor({
  draft, onChange, isNew,
}: { draft: MoleculeDraft; onChange: (patch: Partial<MoleculeDraft>) => void; isNew: boolean }) {
  const { t } = useI18n();
  const [deriving, setDeriving] = useState(false);
  const [deriveError, setDeriveError] = useState<string | null>(null);

  async function deriveAtoms() {
    setDeriving(true);
    setDeriveError(null);
    try {
      const parsed = await parseFormula(draft.formula);
      onChange({ atom_inventory: parsed.atoms, atom_symbols: expandInventory(parsed.atoms) });
    } catch (caught) {
      setDeriveError(getApiErrorMessage(caught));
    } finally {
      setDeriving(false);
    }
  }

  return (
    <div className="molecule-data-tab-grid">
      <TextField id="identity-id" label={t("moleculeData.identity.id")} value={draft.id}
        onChange={(value) => onChange({ id: value })} required />
      <TextField id="identity-formula" label={t("moleculeData.identity.formula")} value={draft.formula}
        onChange={(value) => onChange({ formula: value })} required />
      <div className="molecule-data-field">
        <label htmlFor="identity-charge">{t("moleculeData.identity.charge")}</label>
        <input id="identity-charge" type="number" value={draft.charge}
          onChange={(event) => onChange({ charge: Number(event.target.value) || 0 })} />
      </div>
      <TextField id="identity-name-en" label={t("moleculeData.identity.nameEn")} value={draft.name_en}
        onChange={(value) => onChange({ name_en: value })} />
      <TextField id="identity-name-vi" label={t("moleculeData.identity.nameVi")} value={draft.name_vi}
        onChange={(value) => onChange({ name_vi: value })} />
      <TextField id="identity-aliases" label={t("moleculeData.identity.aliases")} value={draft.aliases.join(", ")}
        onChange={(value) => onChange({ aliases: value.split(",").map((item) => item.trim()).filter(Boolean) })} />
      <TextField id="identity-cas" label={t("moleculeData.identity.casRn")} value={draft.cas_rn ?? ""}
        onChange={(value) => onChange({ cas_rn: value || null })} />
      <div className="molecule-data-field">
        <label htmlFor="identity-pubchem">{t("moleculeData.identity.pubchemCid")}</label>
        <input id="identity-pubchem" type="number" value={draft.pubchem_cid ?? ""}
          onChange={(event) => onChange({ pubchem_cid: event.target.value ? Number(event.target.value) : null })} />
      </div>
      <TextField id="identity-smiles" label={t("moleculeData.identity.smiles")} value={draft.smiles ?? ""}
        onChange={(value) => onChange({ smiles: value || null })} />
      <TextField id="identity-inchi" label={t("moleculeData.identity.inchi")} value={draft.inchi ?? ""}
        onChange={(value) => onChange({ inchi: value || null })} />
      <TextField id="identity-inchikey" label={t("moleculeData.identity.inchikey")} value={draft.inchikey ?? ""}
        onChange={(value) => onChange({ inchikey: value || null })} />

      <div className="molecule-data-field molecule-data-field-wide">
        <label>{t("moleculeData.identity.atomInventory")}</label>
        <div className="molecule-data-inventory-row">
          {Object.entries(draft.atom_inventory).length === 0 && <span className="muted">{t("moleculeData.identity.noInventory")}</span>}
          {Object.entries(draft.atom_inventory).map(([symbol, count]) => (
            <span key={symbol} className="molecule-data-chip">{symbol}<sub>{count}</sub></span>
          ))}
          <button type="button" onClick={deriveAtoms} disabled={deriving || !draft.formula}>
            {deriving ? t("moleculeData.identity.deriving") : t("moleculeData.identity.derive")}
          </button>
        </div>
        {deriveError && <p className="admin-login-error">{deriveError}</p>}
      </div>
      <TextField id="identity-central-atom" label={t("moleculeData.identity.centralAtom")} value={draft.central_atom}
        onChange={(value) => onChange({ central_atom: value })} />
      {!isNew && <p className="muted molecule-data-hint">{t("moleculeData.identity.idLocked")}</p>}
    </div>
  );
}

function expandInventory(atoms: Record<string, number>): string[] {
  const symbols: string[] = [];
  for (const [symbol, count] of Object.entries(atoms)) {
    for (let i = 0; i < count; i += 1) symbols.push(symbol);
  }
  return symbols;
}
