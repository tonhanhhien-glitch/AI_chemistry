import type { AnalysisResult } from "../../types/analysis";

export default function PipelineSummary({ result }: { result: AnalysisResult }) {
  return <div className="pipeline-summary"><div><span>Chất</span><strong>{result.molecule.formula}</strong><small>{result.molecule.name_vi}</small></div><div><span>Phân loại</span><strong>{result.vsepr.ax_en}</strong><small>{result.vsepr.bonding_domains} liên kết · {result.vsepr.lone_pair_domains} cặp tự do</small></div><div><span>Hình học</span><strong>{result.vsepr.molecular_geometry_vi}</strong><small>{result.vsepr.ideal_angle}</small></div></div>;
}
