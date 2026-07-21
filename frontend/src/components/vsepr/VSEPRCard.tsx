import type { VseprResult } from "../../types/vsepr";
import AXENotationBadge from "./AXENotationBadge";
import ElectronDomainTable from "./ElectronDomainTable";
import GeometryCard from "./GeometryCard";

export default function VSEPRCard({ result }: { result: VseprResult }) {
  return <div className="vsepr-card"><div className="notation-row"><AXENotationBadge notation={result.ax_en} /><p>Đếm miền quanh nguyên tử trung tâm; liên kết bội vẫn là một miền.</p></div><ElectronDomainTable result={result} /><div className="geometry-grid"><GeometryCard title="Hình học miền electron" geometry={result.electron_geometry} geometryVi={result.electron_geometry_vi} /><GeometryCard title="Hình học phân tử" geometry={result.molecular_geometry} geometryVi={result.molecular_geometry_vi} angle={result.ideal_angle} /></div>{result.distortion_note_vi && <p className="callout">{result.distortion_note_vi}</p>}<p>{result.teaching_note_vi}</p>{result.pedagogical_hybridization && <p className="muted">Nhãn sư phạm: <strong>{result.pedagogical_hybridization}</strong>. {result.hybridization_warning_vi}</p>}</div>;
}
