import { useI18n } from "../../i18n";
import type { NormalizedProperty, PropertyCategory, PropertyEvidenceType } from "../../types/properties";

const CATEGORIES: PropertyCategory[] = ["identity", "structural", "physical", "chemical"];
const EVIDENCE_TYPES: PropertyEvidenceType[] = ["experimental", "source_annotation", "computed", "curated", "deterministic"];

function newProperty(): NormalizedProperty {
  return {
    key: "", category: "physical", label_vi: "", label_en: "", value: "",
    value_vi: null, value_en: null, unit: null, uncertainty: null,
    conditions: null, phase: null, evidence_type: "curated",
    source_name: "", source_name_vi: null, source_name_en: null,
    source_reference: null, source_url: null, applicability: "applicable",
    retrieved_at: null, notes_vi: null, notes_en: null, observations: [],
  };
}

export default function PropertyEditor({
  properties, onChange,
}: { properties: NormalizedProperty[]; onChange: (properties: NormalizedProperty[]) => void }) {
  const { t } = useI18n();

  function update(index: number, patch: Partial<NormalizedProperty>) {
    const next = [...properties];
    next[index] = { ...next[index], ...patch };
    onChange(next);
  }
  function remove(index: number) {
    onChange(properties.filter((_, i) => i !== index));
  }

  return (
    <div className="molecule-data-tab">
      <p className="muted">{t("moleculeData.properties.hint")}</p>
      {properties.map((property, index) => (
        <fieldset key={index} className="molecule-data-property-card">
          <legend>{property.key || t("moleculeData.properties.untitled")}</legend>
          <div className="molecule-data-tab-grid">
            <div className="molecule-data-field">
              <label>{t("moleculeData.properties.key")}</label>
              <input value={property.key} onChange={(event) => update(index, { key: event.target.value })} />
            </div>
            <div className="molecule-data-field">
              <label>{t("moleculeData.properties.category")}</label>
              <select value={property.category} onChange={(event) => update(index, { category: event.target.value as PropertyCategory })}>
                {CATEGORIES.map((category) => <option key={category} value={category}>{category}</option>)}
              </select>
            </div>
            <div className="molecule-data-field">
              <label>{t("moleculeData.properties.labelEn")}</label>
              <input value={property.label_en} onChange={(event) => update(index, { label_en: event.target.value })} />
            </div>
            <div className="molecule-data-field">
              <label>{t("moleculeData.properties.labelVi")}</label>
              <input value={property.label_vi} onChange={(event) => update(index, { label_vi: event.target.value })} />
            </div>
            <div className="molecule-data-field">
              <label>{t("moleculeData.properties.value")}</label>
              <input value={property.value ?? ""} onChange={(event) => update(index, { value: event.target.value })} />
            </div>
            <div className="molecule-data-field">
              <label>{t("moleculeData.properties.unit")}</label>
              <input value={property.unit ?? ""} onChange={(event) => update(index, { unit: event.target.value || null })} />
            </div>
            <div className="molecule-data-field">
              <label>{t("moleculeData.properties.uncertainty")}</label>
              <input value={property.uncertainty ?? ""} onChange={(event) => update(index, { uncertainty: event.target.value || null })} />
            </div>
            <div className="molecule-data-field">
              <label>{t("moleculeData.properties.phase")}</label>
              <input value={property.phase ?? ""} onChange={(event) => update(index, { phase: event.target.value || null })} />
            </div>
            <div className="molecule-data-field">
              <label>{t("moleculeData.properties.evidenceType")}</label>
              <select value={property.evidence_type} onChange={(event) => update(index, { evidence_type: event.target.value as PropertyEvidenceType })}>
                {EVIDENCE_TYPES.map((evidenceType) => <option key={evidenceType} value={evidenceType}>{evidenceType}</option>)}
              </select>
            </div>
            <div className="molecule-data-field">
              <label>{t("moleculeData.properties.sourceName")}</label>
              <input value={property.source_name} onChange={(event) => update(index, { source_name: event.target.value })} />
            </div>
            <div className="molecule-data-field molecule-data-field-wide">
              <label>{t("moleculeData.properties.conditionsNote")}</label>
              <input value={property.conditions?.note ?? ""} onChange={(event) => update(index, {
                conditions: { temperature: property.conditions?.temperature ?? null, pressure: property.conditions?.pressure ?? null, solvent: property.conditions?.solvent ?? null, note: event.target.value || null },
              })} />
            </div>
            <div className="molecule-data-field molecule-data-field-wide">
              <label>{t("moleculeData.properties.notesEn")}</label>
              <textarea value={property.notes_en ?? ""} onChange={(event) => update(index, { notes_en: event.target.value || null })} />
              <label>{t("moleculeData.properties.notesVi")}</label>
              <textarea value={property.notes_vi ?? ""} onChange={(event) => update(index, { notes_vi: event.target.value || null })} />
            </div>
          </div>
          <button type="button" onClick={() => remove(index)}>{t("moleculeData.actions.remove")}</button>
        </fieldset>
      ))}
      <button type="button" onClick={() => onChange([...properties, newProperty()])}>{t("moleculeData.properties.add")}</button>
    </div>
  );
}
