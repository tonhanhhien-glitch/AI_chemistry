import { useI18n } from "../../i18n";
import type { MolecularGeometryEvidenceDraft, MoleculeDraft } from "../../types/moleculeAdmin";
import { emptyGeometryDraft, localId } from "./defaults";

type Geometry = MolecularGeometryEvidenceDraft;

export default function GeometryEditor({
  geometry, onChange, draft,
}: { geometry: Geometry | null; onChange: (geometry: Geometry | null) => void; draft: MoleculeDraft }) {
  const { t } = useI18n();

  if (!geometry) {
    return (
      <div className="molecule-data-tab">
        <p className="muted">{t("moleculeData.geometry.none")}</p>
        <button type="button" onClick={() => onChange(emptyGeometryDraft(draft.formula, draft.charge))}>
          {t("moleculeData.geometry.add")}
        </button>
      </div>
    );
  }

  function patch(next: Partial<Geometry>) {
    onChange({ ...geometry!, ...next });
  }
  function syncAtomsFromLewis() {
    patch({
      atoms: draft.atom_symbols.map((element, index) => ({
        id: `a${index}`, element, role: index === 0 ? "center" : "ligand",
      })),
      bonds: draft.bond_orders.map((order, index) => ({ atom1_id: "a0", atom2_id: `a${index + 1}`, order })),
    });
  }

  return (
    <div className="molecule-data-tab">
      <div className="molecule-data-actions-row">
        <button type="button" onClick={syncAtomsFromLewis}>{t("moleculeData.geometry.syncAtoms")}</button>
        <button type="button" onClick={() => onChange(null)}>{t("moleculeData.geometry.remove")}</button>
      </div>

      <div className="molecule-data-tab-grid">
        <div className="molecule-data-field">
          <label htmlFor="geo-phase">{t("moleculeData.geometry.phase")}</label>
          <input id="geo-phase" value={geometry.phase ?? ""} onChange={(event) => patch({ phase: event.target.value || null })} />
        </div>
        <div className="molecule-data-field">
          <label htmlFor="geo-state">{t("moleculeData.geometry.electronicState")}</label>
          <input id="geo-state" value={geometry.electronic_state ?? ""} onChange={(event) => patch({ electronic_state: event.target.value || null })} />
        </div>
        <div className="molecule-data-field">
          <label htmlFor="geo-point-group">{t("moleculeData.geometry.pointGroup")}</label>
          <input id="geo-point-group" value={geometry.point_group ?? ""} onChange={(event) => patch({ point_group: event.target.value || null })} />
        </div>
      </div>

      <h3>{t("moleculeData.geometry.atoms")}</h3>
      <table className="molecule-data-table">
        <thead><tr><th>id</th><th>{t("moleculeData.lewis.element")}</th><th>role</th><th /></tr></thead>
        <tbody>
          {geometry.atoms.map((atom, index) => (
            <tr key={index}>
              <td><input value={atom.id} onChange={(event) => {
                const next = [...geometry.atoms]; next[index] = { ...atom, id: event.target.value }; patch({ atoms: next });
              }} /></td>
              <td><input value={atom.element} onChange={(event) => {
                const next = [...geometry.atoms]; next[index] = { ...atom, element: event.target.value }; patch({ atoms: next });
              }} /></td>
              <td>
                <select value={atom.role} onChange={(event) => {
                  const next = [...geometry.atoms]; next[index] = { ...atom, role: event.target.value as typeof atom.role }; patch({ atoms: next });
                }}>
                  <option value="center">center</option>
                  <option value="ligand">ligand</option>
                  <option value="other">other</option>
                </select>
              </td>
              <td><button type="button" onClick={() => patch({ atoms: geometry.atoms.filter((_, i) => i !== index) })}>{t("moleculeData.actions.remove")}</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      <button type="button" onClick={() => patch({ atoms: [...geometry.atoms, { id: localId("a"), element: "", role: "ligand" }] })}>
        {t("moleculeData.geometry.addAtom")}
      </button>

      <h3>{t("moleculeData.geometry.bondAngles")}</h3>
      <p className="muted">{t("moleculeData.geometry.bondAnglesHint")}</p>
      <table className="molecule-data-table">
        <thead><tr><th>atom1</th><th>center</th><th>atom2</th><th>°</th><th>{t("moleculeData.geometry.equivalentCount")}</th><th>{t("moleculeData.geometry.label")}</th><th /></tr></thead>
        <tbody>
          {geometry.bond_angles.map((angle, index) => (
            <tr key={angle.id || index}>
              {(["atom1_id", "center_atom_id", "atom2_id"] as const).map((field) => (
                <td key={field}><input value={angle[field]} onChange={(event) => {
                  const next = [...geometry.bond_angles]; next[index] = { ...angle, [field]: event.target.value }; patch({ bond_angles: next });
                }} /></td>
              ))}
              <td><input type="number" step="0.01" value={angle.value_deg} onChange={(event) => {
                const next = [...geometry.bond_angles]; next[index] = { ...angle, value_deg: Number(event.target.value) || 0 }; patch({ bond_angles: next });
              }} /></td>
              <td><input type="number" min={1} value={angle.equivalent_count} onChange={(event) => {
                const next = [...geometry.bond_angles]; next[index] = { ...angle, equivalent_count: Number(event.target.value) || 1 }; patch({ bond_angles: next });
              }} /></td>
              <td><input value={angle.label ?? ""} onChange={(event) => {
                const next = [...geometry.bond_angles]; next[index] = { ...angle, label: event.target.value || null }; patch({ bond_angles: next });
              }} /></td>
              <td><button type="button" onClick={() => patch({ bond_angles: geometry.bond_angles.filter((_, i) => i !== index) })}>{t("moleculeData.actions.remove")}</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      <button type="button" onClick={() => patch({
        bond_angles: [...geometry.bond_angles, {
          id: localId("angle"), atom1_id: "", center_atom_id: "", atom2_id: "", value_deg: 109.5,
          uncertainty_deg: null, equivalent_count: 1, label: null, source: null,
        }],
      })}>
        {t("moleculeData.geometry.addAngle")}
      </button>

      <h3>{t("moleculeData.geometry.bondLengths")}</h3>
      <table className="molecule-data-table">
        <thead><tr><th>atom1</th><th>atom2</th><th>Å</th><th>{t("moleculeData.geometry.equivalentCount")}</th><th>{t("moleculeData.geometry.label")}</th><th /></tr></thead>
        <tbody>
          {geometry.bond_lengths.map((length, index) => (
            <tr key={length.id || index}>
              {(["atom1_id", "atom2_id"] as const).map((field) => (
                <td key={field}><input value={length[field]} onChange={(event) => {
                  const next = [...geometry.bond_lengths]; next[index] = { ...length, [field]: event.target.value }; patch({ bond_lengths: next });
                }} /></td>
              ))}
              <td><input type="number" step="0.001" value={length.value_angstrom} onChange={(event) => {
                const next = [...geometry.bond_lengths]; next[index] = { ...length, value_angstrom: Number(event.target.value) || 0 }; patch({ bond_lengths: next });
              }} /></td>
              <td><input type="number" min={1} value={length.equivalent_count} onChange={(event) => {
                const next = [...geometry.bond_lengths]; next[index] = { ...length, equivalent_count: Number(event.target.value) || 1 }; patch({ bond_lengths: next });
              }} /></td>
              <td><input value={length.label ?? ""} onChange={(event) => {
                const next = [...geometry.bond_lengths]; next[index] = { ...length, label: event.target.value || null }; patch({ bond_lengths: next });
              }} /></td>
              <td><button type="button" onClick={() => patch({ bond_lengths: geometry.bond_lengths.filter((_, i) => i !== index) })}>{t("moleculeData.actions.remove")}</button></td>
            </tr>
          ))}
        </tbody>
      </table>
      <button type="button" onClick={() => patch({
        bond_lengths: [...geometry.bond_lengths, {
          id: localId("length"), atom1_id: "", atom2_id: "", value_angstrom: 1.0,
          uncertainty_angstrom: null, equivalent_count: 1, label: null, source: null,
        }],
      })}>
        {t("moleculeData.geometry.addLength")}
      </button>

      <h3>{t("moleculeData.sourceReview.title")}</h3>
      <div className="molecule-data-tab-grid">
        <div className="molecule-data-field">
          <label htmlFor="geo-source-name">{t("moleculeData.sourceReview.sourceName")}</label>
          <input id="geo-source-name" value={geometry.source.name} onChange={(event) => patch({ source: { ...geometry.source, name: event.target.value } })} />
        </div>
        <div className="molecule-data-field">
          <label htmlFor="geo-source-ref">{t("moleculeData.sourceReview.reference")}</label>
          <input id="geo-source-ref" value={geometry.source.reference ?? ""} onChange={(event) => patch({ source: { ...geometry.source, reference: event.target.value || null } })} />
        </div>
        <div className="molecule-data-field molecule-data-field-wide">
          <label htmlFor="geo-source-url">{t("moleculeData.sourceReview.url")}</label>
          <input id="geo-source-url" value={geometry.source.url ?? ""} onChange={(event) => patch({ source: { ...geometry.source, url: event.target.value || null } })} />
        </div>
        <div className="molecule-data-field molecule-data-field-wide">
          <label htmlFor="geo-source-notes">{t("moleculeData.sourceReview.notes")}</label>
          <textarea id="geo-source-notes" value={geometry.source.comments ?? ""} onChange={(event) => patch({ source: { ...geometry.source, comments: event.target.value || null } })} />
        </div>
      </div>
    </div>
  );
}
