import { useEffect, useMemo } from "react";
import { useI18n } from "../../i18n";
import { useProperties } from "../../hooks/useProperties";
import type { Molecule } from "../../types/molecule";
import type { NormalizedProperty } from "../../types/properties";
import PropertyTable from "./PropertyTable";

/**
 * The property workspace section.
 *
 * The locally computed properties `/analyze` returns inline render immediately, so the
 * section is never empty. Externally sourced physical and chemical properties come from
 * `/properties`, which is only called when this component mounts — and it mounts when
 * the student opens the collapsed section, never as part of the analysis request.
 * Loading and error states stay inside this section so an external outage cannot hide
 * the Lewis structure, the VSEPR table or the 3D model.
 */
export default function PropertySection({
  molecule,
  inlineProperties,
}: {
  molecule: Molecule;
  inlineProperties: NormalizedProperty[];
}) {
  const { t } = useI18n();
  const request = useMemo(
    () => (molecule.pubchem_cid
      ? { formula: molecule.formula, pubchem_cid: molecule.pubchem_cid }
      : molecule.source === "curated"
        ? { molecule_id: molecule.id }
        : { formula: molecule.formula }),
    [molecule.formula, molecule.id, molecule.pubchem_cid, molecule.source],
  );
  const { bundle, error, isLoading, load } = useProperties(request);

  useEffect(() => { void load(); }, [load]);

  return <div className="property-section">
    {isLoading && <p className="muted" role="status">{t("property.loading")}</p>}
    {error && <div className="callout" role="alert">
      <p>{t("property.error")} {error.message}</p>
      <button type="button" className="secondary-button" onClick={() => void load(true)}>{t("property.retry")}</button>
    </div>}
    <PropertyTable
      properties={bundle?.properties ?? inlineProperties}
      statuses={bundle?.statuses ?? []}
      partial={bundle?.partial ?? false}
    />
  </div>;
}
