import { useI18n } from "../../i18n";
import type { MoleculeDraft } from "../../types/moleculeAdmin";

function TextField({ id, label, value, onChange, wide }: {
  id: string; label: string; value: string; onChange: (value: string) => void; wide?: boolean;
}) {
  return (
    <div className={wide ? "molecule-data-field molecule-data-field-wide" : "molecule-data-field"}>
      <label htmlFor={id}>{label}</label>
      <input id={id} value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

export default function VseprEditor({
  draft, onChange, onAutoCalculate, onValidate, autoCalculating,
}: {
  draft: MoleculeDraft;
  onChange: (patch: Partial<MoleculeDraft>) => void;
  onAutoCalculate: () => void;
  onValidate: () => void;
  autoCalculating: boolean;
}) {
  const { t } = useI18n();
  const impliedSteric = draft.bonding_domains + draft.lone_pair_domains;
  const stericMismatch = impliedSteric !== draft.steric_number;

  return (
    <div className="molecule-data-tab">
      <div className="molecule-data-actions-row">
        <button type="button" onClick={onAutoCalculate} disabled={autoCalculating || !draft.formula}>
          {autoCalculating ? t("moleculeData.lewis.calculating") : t("moleculeData.vsepr.deriveFromLewis")}
        </button>
        <button type="button" onClick={onValidate}>{t("moleculeData.actions.validate")}</button>
      </div>

      <div className="molecule-data-tab-grid">
        <div className="molecule-data-field">
          <label htmlFor="vsepr-bonding">{t("moleculeData.vsepr.bondingDomains")}</label>
          <input id="vsepr-bonding" type="number" min={0} value={draft.bonding_domains}
            onChange={(event) => onChange({ bonding_domains: Number(event.target.value) || 0 })} />
        </div>
        <div className="molecule-data-field">
          <label htmlFor="vsepr-lone">{t("moleculeData.vsepr.lonePairDomains")}</label>
          <input id="vsepr-lone" type="number" min={0} value={draft.lone_pair_domains}
            onChange={(event) => onChange({ lone_pair_domains: Number(event.target.value) || 0 })} />
        </div>
        <div className="molecule-data-field">
          <label htmlFor="vsepr-steric">{t("moleculeData.vsepr.stericNumber")}</label>
          <input id="vsepr-steric" type="number" min={0} value={draft.steric_number}
            onChange={(event) => onChange({ steric_number: Number(event.target.value) || 0 })} />
          {stericMismatch && (
            <p className="admin-login-error">{t("moleculeData.vsepr.stericMismatch", { implied: impliedSteric })}</p>
          )}
        </div>
        <TextField id="vsepr-ax" label={t("moleculeData.vsepr.axEn")} value={draft.ax_en}
          onChange={(value) => onChange({ ax_en: value })} />
        <TextField id="vsepr-electron-geo" label={t("moleculeData.vsepr.electronGeometry")} value={draft.electron_geometry}
          onChange={(value) => onChange({ electron_geometry: value })} />
        <TextField id="vsepr-electron-geo-vi" label={t("moleculeData.vsepr.electronGeometryVi")} value={draft.electron_geometry_vi}
          onChange={(value) => onChange({ electron_geometry_vi: value })} />
        <TextField id="vsepr-mol-geo" label={t("moleculeData.vsepr.molecularGeometry")} value={draft.molecular_geometry}
          onChange={(value) => onChange({ molecular_geometry: value })} />
        <TextField id="vsepr-mol-geo-vi" label={t("moleculeData.vsepr.molecularGeometryVi")} value={draft.molecular_geometry_vi}
          onChange={(value) => onChange({ molecular_geometry_vi: value })} />
        <TextField id="vsepr-ideal-angle" label={t("moleculeData.vsepr.idealAngle")} value={draft.ideal_angle}
          onChange={(value) => onChange({ ideal_angle: value })} />
        <TextField id="vsepr-hybridization" label={t("moleculeData.vsepr.hybridization")} value={draft.hybridization ?? ""}
          onChange={(value) => onChange({ hybridization: value || null })} />
      </div>

      <div className="molecule-data-tab-grid">
        <div className="molecule-data-field molecule-data-field-wide">
          <label htmlFor="vsepr-distortion-en">{t("moleculeData.vsepr.distortionNoteEn")}</label>
          <textarea id="vsepr-distortion-en" value={draft.distortion_note_en ?? ""}
            onChange={(event) => onChange({ distortion_note_en: event.target.value || null })} />
          <label htmlFor="vsepr-distortion-vi">{t("moleculeData.vsepr.distortionNoteVi")}</label>
          <textarea id="vsepr-distortion-vi" value={draft.distortion_note_vi ?? ""}
            onChange={(event) => onChange({ distortion_note_vi: event.target.value || null })} />
        </div>
        <div className="molecule-data-field molecule-data-field-wide">
          <label htmlFor="vsepr-polarity-en">{t("moleculeData.vsepr.polarityNoteEn")}</label>
          <textarea id="vsepr-polarity-en" value={draft.polarity_note_en ?? ""}
            onChange={(event) => onChange({ polarity_note_en: event.target.value || null })} />
          <label htmlFor="vsepr-polarity-vi">{t("moleculeData.vsepr.polarityNoteVi")}</label>
          <textarea id="vsepr-polarity-vi" value={draft.polarity_note_vi ?? ""}
            onChange={(event) => onChange({ polarity_note_vi: event.target.value || null })} />
        </div>
      </div>
    </div>
  );
}
