import { useEffect, useState } from "react";
import { getExamples, getVseprRules, type VseprRuleRecord } from "../api/moleculeApi";
import PageContainer from "../components/layout/PageContainer";
import GeometryIcon from "../components/vsepr/GeometryIcon";
import type { MoleculeSummary } from "../types/molecule";

export default function RulesPage() {
  const [rules, setRules] = useState<VseprRuleRecord[]>([]); const [examples, setExamples] = useState<MoleculeSummary[]>([]); const [error, setError] = useState("");
  useEffect(() => { void Promise.all([getVseprRules(), getExamples()]).then(([ruleRows, exampleRows]) => { setRules(ruleRows); setExamples(exampleRows); }).catch(() => setError("Không tải được bảng quy tắc.")); }, []);
  return <PageContainer><header className="page-intro"><p className="eyebrow">Bảng tra cứu</p><h1>Quy tắc VSEPR</h1><p>Mỗi liên kết đơn, đôi hoặc ba tính là một miền electron quanh nguyên tử trung tâm.</p></header>{error && <p className="error-message">{error}</p>}<div className="rules-grid">{rules.map((rule) => <article className="rule-card" key={rule.ax_en}><GeometryIcon geometry={rule.molecular_geometry} label={rule.molecular_geometry_vi} /><div><strong>{rule.ax_en}</strong><p>{rule.bonding_domains} miền liên kết · {rule.lone_pair_domains} cặp tự do</p><dl><dt>Miền electron</dt><dd>{rule.electron_geometry_vi}</dd><dt>Phân tử</dt><dd>{rule.molecular_geometry_vi}</dd><dt>Góc</dt><dd>{rule.ideal_angle}</dd><dt>Ví dụ</dt><dd>{examples.filter((item) => item.ax_en === rule.ax_en).map((item) => item.formula).join(", ") || "—"}</dd></dl><small>{rule.teaching_note_vi}</small></div></article>)}</div><p className="offline-notice">Các nhãn sp³d/sp³d² nếu xuất hiện chỉ là gần đúng sư phạm kiểu VSEPR, không phải mô tả liên kết hiện đại đầy đủ.</p></PageContainer>;
}
