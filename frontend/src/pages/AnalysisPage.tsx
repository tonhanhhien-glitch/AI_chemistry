import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { searchMolecules } from "../api/moleculeApi";
import ExplanationPanel from "../components/explanation/ExplanationPanel";
import FeedbackForm from "../components/feedback/FeedbackForm";
import FormulaInput from "../components/input/FormulaInput";
import InputValidationMessage from "../components/input/InputValidationMessage";
import PageContainer from "../components/layout/PageContainer";
import LewisViewer from "../components/lewis/LewisViewer";
import PropertyTable from "../components/properties/PropertyTable";
import TeachingNoteCard from "../components/properties/TeachingNoteCard";
import Molecule3DViewer from "../components/viewer3d/Molecule3DViewer";
import VSEPRCard from "../components/vsepr/VSEPRCard";
import PipelineSummary from "../components/workflow/PipelineSummary";
import StepCard from "../components/workflow/StepCard";
import WorkflowStepper from "../components/workflow/WorkflowStepper";
import { useAnalyzeMolecule } from "../hooks/useAnalyzeMolecule";

export default function AnalysisPage() {
  const [params] = useSearchParams();
  const initialId = params.get("id"); const initialFormula = params.get("formula");
  const [query, setQuery] = useState(initialFormula || ""); const [localError, setLocalError] = useState("");
  const { result, error, isLoading, run } = useAnalyzeMolecule();
  useEffect(() => { if (initialId) void run({ molecule_id: initialId, include_explanation: true }); else if (initialFormula) void run({ formula: initialFormula, include_explanation: true }); }, [initialFormula, initialId, run]);
  async function submit() {
    setLocalError(""); const value = query.trim();
    if (!value) { setLocalError("Vui lòng nhập công thức hoặc tên chất."); return; }
    if (/^[A-Z]/.test(value)) { void run({ formula: value, include_explanation: true }); return; }
    try { const matches = await searchMolecules(value); if (matches.length === 1) void run({ molecule_id: matches[0].id, include_explanation: true }); else if (matches.length > 1) setLocalError("Có nhiều kết quả. Hãy nhập công thức hoặc tên đầy đủ hơn."); else setLocalError("Không tìm thấy chất đã tuyển chọn phù hợp."); }
    catch { setLocalError("Không thể tìm tên chất. Hãy thử nhập công thức."); }
  }
  return <PageContainer><header className="page-intro"><p className="eyebrow">Phòng học phân tử</p><h1>Phân tích từng bước</h1><p>Kiểm tra từng lớp biểu diễn, từ electron hoá trị đến mô hình không gian.</p></header><div className="analysis-input-card"><FormulaInput value={query} onChange={setQuery} onSubmit={submit} loading={isLoading} /><InputValidationMessage message={localError || error?.message} />{error?.candidates && <div className="candidate-list"><p>Chọn cấu tạo:</p>{error.candidates.map((item) => <button key={item.id} onClick={() => void run({ molecule_id: item.id, include_explanation: true })}>{item.formula} — {item.name_vi}</button>)}</div>}{error && <button className="secondary-button" onClick={() => void submit()}>Thử lại</button>}</div>{isLoading && <div className="loading-panel" role="status"><span className="loader" />Đang chạy bộ quy tắc và dựng mô hình…</div>}{result && <><WorkflowStepper /><PipelineSummary result={result} />{result.notices.warnings_vi.map((warning) => <p className="offline-notice" key={warning}>{warning}</p>)}<div className="learning-grid"><StepCard number={2} title="Cấu trúc Lewis"><LewisViewer structure={result.lewis} /></StepCard><StepCard number={3} title="Miền electron & AXnEm"><VSEPRCard result={result.vsepr} /></StepCard><StepCard number={4} title="Mô hình 3D tương tác"><Molecule3DViewer structure={result.structure3d} /></StepCard><StepCard number={5} title="Tính chất & nguồn"><PropertyTable properties={result.properties} /><TeachingNoteCard note={result.vsepr.teaching_note_vi} /></StepCard><StepCard number={6} title="Giải thích sư phạm"><ExplanationPanel key={result.molecule.id} moleculeId={result.molecule.id} initial={result.explanation} /></StepCard><StepCard number={7} title="Phản hồi ẩn danh"><FeedbackForm moleculeId={result.molecule.id} /></StepCard></div></>}</PageContainer>;
}
