import { useI18n } from "../../i18n";
import type { NormalizedProperty, PropertyCategory, PropertyProviderStatus } from "../../types/properties";

const CATEGORY_ORDER: PropertyCategory[] = ["identity", "structural", "physical", "chemical"];

const CATEGORY_LABEL_KEYS: Record<PropertyCategory, string> = {
  identity: "property.category.identity",
  structural: "property.category.structural",
  physical: "property.category.physical",
  chemical: "property.category.chemical",
};

const EVIDENCE_LABEL_KEYS: Record<string, string> = {
  experimental: "property.evidence.experimental",
  computed: "property.evidence.computed",
  curated: "property.evidence.curated",
  deterministic: "property.evidence.deterministic",
};

function formatConditions(property: NormalizedProperty): string | null {
  const parts = [property.conditions?.temperature, property.conditions?.pressure, property.conditions?.solvent, property.phase]
    .filter((value): value is string => Boolean(value));
  return parts.length ? parts.join(" · ") : null;
}

/**
 * Renders the normalized property bundle grouped by category.
 *
 * A property with no value is shown as an explicit "not applicable" or "no data"
 * row with its reason, never blanked out and never filled with a plausible number:
 * a student has to be able to tell "this was not measured" from "this does not apply
 * to an isolated ion".
 */
export default function PropertyTable({
  properties,
  statuses = [],
  partial = false,
}: {
  properties: NormalizedProperty[];
  statuses?: PropertyProviderStatus[];
  partial?: boolean;
}) {
  const { t, lang } = useI18n();
  const en = lang === "en";
  const failed = statuses.filter((status) => !["success", "cache_hit", "disabled"].includes(status.state));

  if (!properties.length) return <p className="muted">{t("property.empty")}</p>;

  return <div className="property-groups">
    {partial && failed.length > 0 && (
      <p className="callout" role="status">
        {t("property.partial")} {failed.map((status) => `${status.service}: ${status.state}`).join(", ")}
      </p>
    )}
    {CATEGORY_ORDER.map((category) => {
      const rows = properties.filter((item) => item.category === category);
      if (!rows.length) return null;
      return <section key={category}>
        <h3>{t(CATEGORY_LABEL_KEYS[category])}</h3>
        <table>
          <tbody>
            {rows.map((item) => {
              const conditions = formatConditions(item);
              const notes = en ? item.notes_en : item.notes_vi;
              return <tr key={item.key} data-applicability={item.applicability}>
                <th scope="row">{en ? item.label_en : item.label_vi}</th>
                <td>
                  {item.applicability === "applicable" ? (
                    <span className="property-value">
                      {item.value}{item.unit ? ` ${item.unit}` : ""}
                      {item.uncertainty ? ` ± ${item.uncertainty}` : ""}
                    </span>
                  ) : (
                    <span className="property-missing">
                      {item.applicability === "not_applicable" ? t("property.notApplicable") : t("property.unavailable")}
                    </span>
                  )}
                  <small className="property-provenance">
                    {t(EVIDENCE_LABEL_KEYS[item.evidence_type] ?? "property.evidence.computed")}
                    {" · "}
                    {item.source_url
                      ? <a href={item.source_url} target="_blank" rel="noreferrer">{item.source_name}</a>
                      : item.source_name}
                    {item.source_reference ? ` · ${item.source_reference}` : ""}
                    {conditions ? ` · ${conditions}` : ""}
                  </small>
                  {notes && <small className="property-note">{notes}</small>}
                </td>
              </tr>;
            })}
          </tbody>
        </table>
      </section>;
    })}
  </div>;
}
