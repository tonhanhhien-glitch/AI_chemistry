import { useI18n } from "../../i18n";
import type { LewisStructure } from "../../types/lewis";
import FormalChargeTable from "./FormalChargeTable";
import LewisSvgRenderer from "./LewisSvgRenderer";
import ResonanceNote from "./ResonanceNote";

export default function LewisViewer({ structure }: { structure: LewisStructure }) {
  const { t } = useI18n();
  return <div className="lewis-viewer"><LewisSvgRenderer structure={structure} /><div><dl className="fact-list"><div><dt>{t("lewis.totalValence")}</dt><dd>{structure.total_valence_electrons}</dd></div><div><dt>{t("lewis.source")}</dt><dd>{structure.source}</dd></div></dl>{structure.exception_flags.note_vi && <p className="warning-note">{structure.exception_flags.note_vi}</p>}<ResonanceNote forms={structure.resonance_forms} note={structure.resonance_note_vi} /><details><summary>{t("lewis.showFormalCharge")}</summary><FormalChargeTable structure={structure} /></details></div></div>;
}
