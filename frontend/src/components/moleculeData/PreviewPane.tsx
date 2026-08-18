import { useI18n } from "../../i18n";
import LewisViewer from "../lewis/LewisViewer";
import VSEPRCard from "../vsepr/VSEPRCard";
import Molecule3DViewer from "../viewer3d/Molecule3DViewer";
import PropertyTable from "../properties/PropertyTable";
import type { AnalysisResult } from "../../types/analysis";

export default function PreviewPane({ preview }: { preview: AnalysisResult | null }) {
  const { t, lang } = useI18n();
  if (!preview) return null;
  const warnings = lang === "vi" ? preview.notices.warnings_vi : preview.notices.warnings_en;
  return (
    <div className="molecule-data-preview">
      <h3>{t("moleculeData.preview.title")}</h3>
      {warnings.length > 0 && (
        <ul className="molecule-data-preview-warnings">
          {warnings.map((warning, index) => <li key={index}>{warning}</li>)}
        </ul>
      )}
      <div className="molecule-data-preview-grid">
        <LewisViewer structure={preview.lewis} />
        <Molecule3DViewer structure={preview.structure3d} />
      </div>
      <VSEPRCard result={preview.vsepr} angles={preview.bond_angles} />
      <PropertyTable properties={preview.properties} />
    </div>
  );
}
