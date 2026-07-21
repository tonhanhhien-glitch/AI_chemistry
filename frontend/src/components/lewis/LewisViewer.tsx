import type { LewisStructure } from "../../types/lewis";
import FormalChargeTable from "./FormalChargeTable";
import LewisSvgRenderer from "./LewisSvgRenderer";
import ResonanceNote from "./ResonanceNote";

export default function LewisViewer({ structure }: { structure: LewisStructure }) {
  return <div className="lewis-viewer"><LewisSvgRenderer structure={structure} /><div><dl className="fact-list"><div><dt>Tổng electron hoá trị</dt><dd>{structure.total_valence_electrons}</dd></div><div><dt>Nguồn cấu trúc</dt><dd>{structure.source}</dd></div></dl>{structure.exception_flags.note_vi && <p className="warning-note">{structure.exception_flags.note_vi}</p>}<ResonanceNote forms={structure.resonance_forms} note={structure.resonance_note_vi} /><details><summary>Xem điện tích hình thức</summary><FormalChargeTable structure={structure} /></details></div></div>;
}
