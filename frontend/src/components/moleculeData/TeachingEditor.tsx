import { useI18n } from "../../i18n";
import type { MoleculeDraft } from "../../types/moleculeAdmin";

function BilingualField({ idBase, label, en, vi, onChangeEn, onChangeVi }: {
  idBase: string; label: string; en: string; vi: string;
  onChangeEn: (value: string) => void; onChangeVi: (value: string) => void;
}) {
  return (
    <fieldset className="molecule-data-field molecule-data-field-wide">
      <legend>{label}</legend>
      <label htmlFor={`${idBase}-en`}>English</label>
      <textarea id={`${idBase}-en`} value={en} onChange={(event) => onChangeEn(event.target.value)} />
      <label htmlFor={`${idBase}-vi`}>Tiếng Việt</label>
      <textarea id={`${idBase}-vi`} value={vi} onChange={(event) => onChangeVi(event.target.value)} />
    </fieldset>
  );
}

export default function TeachingEditor({ draft, onChange }: { draft: MoleculeDraft; onChange: (patch: Partial<MoleculeDraft>) => void }) {
  const { t } = useI18n();
  return (
    <div className="molecule-data-tab">
      <BilingualField
        idBase="teaching-general" label={t("moleculeData.teaching.general")}
        en={draft.teaching_note_en ?? ""} vi={draft.teaching_note_vi ?? ""}
        onChangeEn={(value) => onChange({ teaching_note_en: value || null })}
        onChangeVi={(value) => onChange({ teaching_note_vi: value || null })}
      />
      <BilingualField
        idBase="teaching-resonance" label={t("moleculeData.teaching.resonance")}
        en={draft.resonance_note_en ?? ""} vi={draft.resonance_note_vi ?? ""}
        onChangeEn={(value) => onChange({ resonance_note_en: value || null })}
        onChangeVi={(value) => onChange({ resonance_note_vi: value || null })}
      />
      <BilingualField
        idBase="teaching-misconception" label={t("moleculeData.teaching.misconception")}
        en={draft.misconception_note_en ?? ""} vi={draft.misconception_note_vi ?? ""}
        onChangeEn={(value) => onChange({ misconception_note_en: value || null })}
        onChangeVi={(value) => onChange({ misconception_note_vi: value || null })}
      />
      <BilingualField
        idBase="teaching-structure-property" label={t("moleculeData.teaching.structureProperty")}
        en={draft.structure_property_note_en ?? ""} vi={draft.structure_property_note_vi ?? ""}
        onChangeEn={(value) => onChange({ structure_property_note_en: value || null })}
        onChangeVi={(value) => onChange({ structure_property_note_vi: value || null })}
      />
      <p className="muted">{t("moleculeData.teaching.distortionPolarityHint")}</p>
    </div>
  );
}
