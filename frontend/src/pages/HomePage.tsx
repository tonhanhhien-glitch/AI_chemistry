import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getExamples } from "../api/moleculeApi";
import ExampleMoleculeGrid from "../components/input/ExampleMoleculeGrid";
import FormulaInput from "../components/input/FormulaInput";
import PageContainer from "../components/layout/PageContainer";
import type { MoleculeSummary } from "../types/molecule";

export default function HomePage() {
  const navigate = useNavigate(); const [query, setQuery] = useState(""); const [examples, setExamples] = useState<MoleculeSummary[]>([]);
  useEffect(() => { void getExamples().then((items) => setExamples(items.slice(0, 8))).catch(() => undefined); }, []);
  function select(item: MoleculeSummary) { navigate(`/analysis?id=${encodeURIComponent(item.id)}`); }
  return <PageContainer><section className="hero-grid"><div><p className="eyebrow">Học Lewis · hiểu hình học</p><h1>Từ công thức đến <em>hình dạng phân tử</em></h1><p className="lede">Một quy trình tiếng Việt nối cấu trúc Lewis, miền electron, AXnEm, VSEPR và mô hình 3D. Kết luận hoá học đến từ bộ quy tắc xác định — AI chỉ giải thích.</p><FormulaInput value={query} onChange={setQuery} onSubmit={() => query.trim() && navigate(`/analysis?formula=${encodeURIComponent(query.trim())}`)} /></div><div className="hero-visual" aria-label="Minh hoạ hình học phân tử"><span className="orb orb-a">O</span><span className="bond-line" /><span className="orb orb-c">C</span><span className="bond-line second" /><span className="orb orb-b">O</span><p>CO₂ · AX2 · 180°</p></div></section><section className="trust-strip"><div><strong>100%</strong><span>hoạt động offline với bộ ví dụ</span></div><div><strong>13</strong><span>kiểu AXnEm từ 2–6 miền</span></div><div><strong>0</strong><span>kết luận hoá học do LLM tự quyết</span></div></section><section className="content-section"><div className="section-heading"><div><p className="eyebrow">Bắt đầu nhanh</p><h2>Chất tiêu biểu</h2></div><a href="/examples">Xem tất cả →</a></div>{examples.length ? <ExampleMoleculeGrid examples={examples} onSelect={select} /> : <p className="muted">Khởi động backend để tải bộ ví dụ đã tuyển chọn.</p>}</section><section className="scope-card"><h2>Phạm vi có chủ đích</h2><p>Hỗ trợ phân tử và ion nhóm chính có mô hình Lewis/VSEPR rõ ràng, số miền ≤ 6. Không suy đoán đồng phân chỉ từ công thức, không xử lý phức kim loại chuyển tiếp, hydrate, ngoặc hoặc hệ số trong MVP.</p></section></PageContainer>;
}
