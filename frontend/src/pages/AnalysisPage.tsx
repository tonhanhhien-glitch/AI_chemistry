import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import CollapsibleSection from "../components/analysis/CollapsibleSection";
import WorkspacePane from "../components/analysis/WorkspacePane";
import ChatPane from "../components/chat/ChatPane";
import FormulaInput from "../components/input/FormulaInput";
import InputValidationMessage from "../components/input/InputValidationMessage";
import PageContainer from "../components/layout/PageContainer";
import LewisViewer from "../components/lewis/LewisViewer";
import PropertySection from "../components/properties/PropertySection";
import Molecule3DViewer from "../components/viewer3d/Molecule3DViewer";
import VSEPRCard from "../components/vsepr/VSEPRCard";
import PipelineSummary from "../components/workflow/PipelineSummary";
import { useI18n } from "../i18n";
import { ChemFormula } from "../utils/chemFormula";
import { useAnalyzeMolecule } from "../hooks/useAnalyzeMolecule";
import type { AnalysisRequest } from "../types/analysis";

export default function AnalysisPage() {
  const { t, lang } = useI18n();
  const [params, setSearchParams] = useSearchParams();
  const initialId = params.get("id"); const initialQuery = params.get("q") || params.get("formula");
  const [query, setQuery] = useState(initialQuery || ""); const [localError, setLocalError] = useState("");
  const [infoOpen, setInfoOpen] = useState(true); const [chatOpen, setChatOpen] = useState(true);
  const { result, error, isLoading, run } = useAnalyzeMolecule();
  const skipNextFetch = useRef(false);
  useEffect(() => {
    if (skipNextFetch.current) { skipNextFetch.current = false; return; }
    if (initialId) void run({ molecule_id: initialId, include_explanation: false, language: lang }); else if (initialQuery) void run({ query: initialQuery, include_explanation: false, language: lang });
  }, [initialQuery, initialId, lang, run]);
  function goTo(nextParams: Record<string, string>, request: AnalysisRequest) { skipNextFetch.current = true; setSearchParams(nextParams); void run(request); }
  function submit() {
    setLocalError(""); const value = query.trim();
    if (!value) { setLocalError(t("analysis.error.empty")); return; }
    // The raw query goes to the backend, which decides whether it is a formula or a
    // name. Guessing from capitalisation here misroutes "sulfate" and "Sulfate" alike,
    // and identity resolution is chemistry, not presentation.
    goTo({ q: value }, { query: value, include_explanation: false, language: lang });
  }
  return (
    <PageContainer
      className="analysis-shell"
      headerSearch={
        <FormulaInput
          value={query}
          onChange={setQuery}
          onSubmit={submit}
          onSelectMolecule={(item) => {
            setQuery(item.formula);
            goTo({ molecule: item.id }, { molecule_id: item.id, include_explanation: false, language: lang });
          }}
          loading={isLoading}
        />
      }
    >
      <h1 className="visually-hidden">{t("analysis.title")}</h1>
      {(localError || error) && (
        <div className="analysis-alerts">
          <InputValidationMessage message={localError || error?.message} />
          {error?.candidates && (
            <div className="candidate-list">
              <p>{t("analysis.chooseStructure")}</p>
              {error.candidates.map((item) => {
                const name = lang === "vi" ? item.name_vi || item.name_en : item.name_en || item.name_vi;
                return (
                  <button key={item.id} onClick={() => void run(item.cid ? { query: query.trim(), pubchem_cid: item.cid, include_explanation: false, language: lang } : { molecule_id: item.id, include_explanation: false, language: lang })}><strong>{name}</strong><span><ChemFormula text={item.formula} /> · {t("analysis.candidateCharge")}: {item.charge ?? 0} · CID {item.cid ?? "—"}</span>{item.canonical_smiles && <code>{item.canonical_smiles}</code>}<small>{item.source ?? "Curated"}</small></button>
                );
              })}
            </div>
          )}
          {error && <button className="secondary-button" onClick={() => submit()}>{t("analysis.retry")}</button>}
        </div>
      )}
      {isLoading && <div className="loading-panel" role="status"><span className="loader" />{t("analysis.loading")}</div>}
      {result && (
        <>
          <PipelineSummary result={result} />
          <div className={`analysis-workspace${infoOpen ? "" : " info-collapsed"}${chatOpen ? "" : " chat-collapsed"}`}>
            <WorkspacePane side="left" title={t("analysis.pane.info")} open={infoOpen} onToggle={setInfoOpen}>
              <CollapsibleSection number={2} title={t("analysis.step.lewis")}><LewisViewer structure={result.lewis} /></CollapsibleSection>
              <CollapsibleSection number={3} title={t("analysis.step.domains")} defaultOpen={false}><VSEPRCard result={result.vsepr} angles={result.bond_angles} /></CollapsibleSection>
              <CollapsibleSection number={5} title={t("analysis.step.properties")} defaultOpen={false}>
                <PropertySection key={result.molecule.id} molecule={result.molecule} inlineProperties={result.properties} />
              </CollapsibleSection>
            </WorkspacePane>
            <section className="workspace-main" aria-label={t("analysis.step.model3d")}>
              <header className="workspace-main-head"><h2>{t("analysis.step.model3d")}</h2></header>
              <Molecule3DViewer key={result.molecule.id} structure={result.structure3d} />
            </section>
            <WorkspacePane side="right" title={t("chat.title")} open={chatOpen} onToggle={setChatOpen}>
              <ChatPane moleculeId={result.molecule.id} formula={result.molecule.formula} pubchemCid={result.molecule.pubchem_cid} />
            </WorkspacePane>
          </div>
        </>
      )}
    </PageContainer>
  );
}
