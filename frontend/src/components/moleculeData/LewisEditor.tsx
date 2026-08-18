import { useI18n } from "../../i18n";
import type { MoleculeDraft } from "../../types/moleculeAdmin";

export default function LewisEditor({
  draft, onChange, onAutoCalculate, onValidate, autoCalculating,
}: {
  draft: MoleculeDraft;
  onChange: (patch: Partial<MoleculeDraft>) => void;
  onAutoCalculate: () => void;
  onValidate: () => void;
  autoCalculating: boolean;
}) {
  const { t } = useI18n();
  const atoms = draft.atom_symbols;

  function updateAtomAt(index: number, symbol: string) {
    const next = [...atoms];
    next[index] = symbol;
    onChange({ atom_symbols: next });
  }
  function updateLonePairAt(index: number, value: number) {
    const next = [...draft.lone_pairs];
    next[index] = value;
    onChange({ lone_pairs: next });
  }
  function updateFormalChargeAt(index: number, value: number) {
    const next = [...draft.formal_charges];
    next[index] = value;
    onChange({ formal_charges: next });
  }
  function updateBondOrderAt(bondIndex: number, value: number) {
    const next = [...draft.bond_orders];
    next[bondIndex] = value;
    onChange({ bond_orders: next });
  }
  function addLigand() {
    onChange({
      atom_symbols: [...atoms, ""],
      lone_pairs: [...draft.lone_pairs, 0],
      formal_charges: [...draft.formal_charges, 0],
      bond_orders: [...draft.bond_orders, 1],
    });
  }
  function removeLigand(index: number) {
    if (index === 0) return;
    onChange({
      atom_symbols: atoms.filter((_, i) => i !== index),
      lone_pairs: draft.lone_pairs.filter((_, i) => i !== index),
      formal_charges: draft.formal_charges.filter((_, i) => i !== index),
      bond_orders: draft.bond_orders.filter((_, i) => i !== index - 1),
    });
  }

  return (
    <div className="molecule-data-tab">
      <div className="molecule-data-actions-row">
        <button type="button" onClick={onAutoCalculate} disabled={autoCalculating || !draft.formula}>
          {autoCalculating ? t("moleculeData.lewis.calculating") : t("moleculeData.lewis.autoCalculate")}
        </button>
        <button type="button" onClick={onValidate}>{t("moleculeData.actions.validate")}</button>
      </div>

      <table className="molecule-data-table">
        <thead>
          <tr>
            <th>{t("moleculeData.lewis.atom")}</th>
            <th>{t("moleculeData.lewis.element")}</th>
            <th>{t("moleculeData.lewis.lonePairs")}</th>
            <th>{t("moleculeData.lewis.formalCharge")}</th>
            <th>{t("moleculeData.lewis.bondOrder")}</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {atoms.map((symbol, index) => (
            <tr key={index}>
              <td>{index === 0 ? t("moleculeData.lewis.center") : `#${index}`}</td>
              <td><input value={symbol} onChange={(event) => updateAtomAt(index, event.target.value)} /></td>
              <td><input type="number" min={0} value={draft.lone_pairs[index] ?? 0}
                onChange={(event) => updateLonePairAt(index, Number(event.target.value) || 0)} /></td>
              <td><input type="number" value={draft.formal_charges[index] ?? 0}
                onChange={(event) => updateFormalChargeAt(index, Number(event.target.value) || 0)} /></td>
              <td>
                {index === 0 ? "—" : (
                  <input type="number" min={1} max={3} value={draft.bond_orders[index - 1] ?? 1}
                    onChange={(event) => updateBondOrderAt(index - 1, Number(event.target.value) || 1)} />
                )}
              </td>
              <td>{index !== 0 && <button type="button" onClick={() => removeLigand(index)}>{t("moleculeData.actions.remove")}</button>}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <button type="button" onClick={addLigand}>{t("moleculeData.lewis.addLigand")}</button>

      <div className="molecule-data-tab-grid">
        <div className="molecule-data-field">
          <label htmlFor="lewis-valence">{t("moleculeData.lewis.totalValence")}</label>
          <input id="lewis-valence" type="number" value={draft.total_valence_electrons}
            onChange={(event) => onChange({ total_valence_electrons: Number(event.target.value) || 0 })} />
        </div>
        <div className="molecule-data-field">
          <label htmlFor="lewis-resonance-forms">{t("moleculeData.lewis.resonanceForms")}</label>
          <input id="lewis-resonance-forms" type="number" min={1} value={draft.resonance_forms}
            onChange={(event) => onChange({ resonance_forms: Number(event.target.value) || 1 })} />
        </div>
      </div>

      <fieldset className="molecule-data-field molecule-data-field-wide">
        <legend>{t("moleculeData.lewis.octetExceptions")}</legend>
        {(["electron_deficient", "expanded_octet", "odd_electron"] as const).map((flag) => (
          <label key={flag} className="molecule-data-checkbox">
            <input
              type="checkbox"
              checked={draft.exception_flags[flag]}
              onChange={(event) => onChange({ exception_flags: { ...draft.exception_flags, [flag]: event.target.checked } })}
            />
            {t(`moleculeData.lewis.flag.${flag}`)}
          </label>
        ))}
      </fieldset>
      <p className="muted">{t("moleculeData.lewis.resonanceNoteHint")}</p>
    </div>
  );
}
