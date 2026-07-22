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
import { useI18n } from "../i18n";
import { useAnalyzeMolecule } from "../hooks/useAnalyzeMolecule";

export default function AnalysisPage() {
  const { t } = useI18n();
  const [params] = useSearchParams();
  const initialId = params.get("id"); const initialFormula = params.get("formula");
  const [query, setQuery] = useState(initialFormula || ""); const [localError, setLocalError] = useState("");
  const { result, error, isLoading, run } = useAnalyzeMolecule();
  useEffect(() => { if (initialId) void run({ molecule_id: initialId, include_explanation: true }); else if (initialFormula) void run({ formula: initialFormula, include_explanation: true }); }, [initialFormula, initialId, run]);
  async function submit() {
    setLocalError(""); const value = query.trim();
    if (!value) { setLocalError(t("analysis.error.empty")); return; }
    if (/^[A-Z]/.test(value)) { void run({ formula: value, include_explanation: true }); return; }
    try { const matches = await searchMolecules(value); if (matches.length === 1) void run({ molecule_id: matches[0].id, include_explanation: true }); else if (matches.length > 1) setLocalError(t("analysis.error.multi")); else setLocalError(t("analysis.error.notFound")); }
    catch { setLocalError(t("analysis.error.searchFail")); }
  }
  return <PageContainer><header className="page-intro"><p className="eyebrow">{t("analysis.eyebrow")}</p><h1>{t("analysis.title")}</h1><p>{t("analysis.intro")}</p></header><div className="analysis-input-card"><FormulaInput value={query} onChange={setQuery} onSubmit={submit} loading={isLoading} /><InputValidationMessage message={localError || error?.message} />{error?.candidates && <div className="candidate-list"><p>{t("analysis.chooseStructure")}</p>{error.candidates.map((item) => <button key={item.id} onClick={() => void run({ molecule_id: item.id, include_explanation: true })}>{item.formula} — {item.name_vi}</button>)}</div>}{error && <button className="secondary-button" onClick={() => void submit()}>{t("analysis.retry")}</button>}</div>{isLoading && <div className="loading-panel" role="status"><span className="loader" />{t("analysis.loading")}</div>}{result && <><WorkflowStepper /><PipelineSummary result={result} />{result.notices.warnings_vi.map((warning) => <p className="offline-notice" key={warning}>{warning}</p>)}<div className="learning-grid"><StepCard number={2} title={t("analysis.step.lewis")}><LewisViewer structure={result.lewis} /></StepCard><StepCard number={3} title={t("analysis.step.domains")}><VSEPRCard result={result.vsepr} /></StepCard><StepCard number={4} title={t("analysis.step.model3d")}><Molecule3DViewer structure={result.structure3d} /></StepCard><StepCard number={5} title={t("analysis.step.properties")}><PropertyTable properties={result.properties} /><TeachingNoteCard note={result.vsepr.teaching_note_vi} /></StepCard><StepCard number={6} title={t("analysis.step.explanation")}><ExplanationPanel key={result.molecule.id} moleculeId={result.molecule.id} initial={result.explanation} /></StepCard><StepCard number={7} title={t("analysis.step.feedback")}><FeedbackForm moleculeId={result.molecule.id} /></StepCard></div></>}</PageContainer>;
}
