import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getExamples } from "../api/moleculeApi";
import ExampleMoleculeGrid from "../components/input/ExampleMoleculeGrid";
import FormulaInput from "../components/input/FormulaInput";
import PageContainer from "../components/layout/PageContainer";
import { useI18n } from "../i18n";
import type { MoleculeSummary } from "../types/molecule";

export default function HomePage() {
  const { t } = useI18n();
  const navigate = useNavigate(); const [query, setQuery] = useState(""); const [examples, setExamples] = useState<MoleculeSummary[]>([]);
  useEffect(() => { void getExamples().then((items) => setExamples(items.slice(0, 8))).catch(() => undefined); }, []);
  function select(item: MoleculeSummary) { navigate(`/analysis?id=${encodeURIComponent(item.id)}`); }
  return <PageContainer><section className="hero">
      <div className="hero-chemistry-bg" aria-hidden="true">
        <div className="chem-glow chem-glow-a" />
        <div className="chem-glow chem-glow-b" />
        <div className="chem-glow chem-glow-c" />
        <svg className="chem-network" viewBox="0 0 700 420" preserveAspectRatio="xMaxYMid slice" focusable="false">
          <g className="chem-bonds">
            <line x1="600" y1="45" x2="660" y2="70" />
            <line x1="660" y1="70" x2="695" y2="150" />
            <line x1="660" y1="70" x2="615" y2="160" />
            <line x1="615" y1="160" x2="540" y2="100" />
            <line x1="615" y1="160" x2="560" y2="210" />
            <line x1="560" y1="210" x2="650" y2="250" />
            <line x1="650" y1="250" x2="600" y2="320" />
            <line x1="560" y1="210" x2="500" y2="280" />
            <line x1="500" y1="280" x2="460" y2="190" />
            <line x1="460" y1="190" x2="540" y2="100" />
            <line x1="460" y1="190" x2="400" y2="130" />
            <line x1="500" y1="280" x2="420" y2="260" />
            <line x1="420" y1="260" x2="330" y2="210" />
            <line x1="460" y1="190" x2="420" y2="260" />
          </g>
          <g className="chem-nodes">
            <circle cx="660" cy="70" r="7" />
            <circle cx="600" cy="45" r="4" />
            <circle cx="695" cy="150" r="9" />
            <circle cx="615" cy="160" r="5" />
            <circle cx="540" cy="100" r="5" />
            <circle cx="560" cy="210" r="6" />
            <circle cx="650" cy="250" r="4" />
            <circle cx="600" cy="320" r="7" />
            <circle cx="500" cy="280" r="4" />
            <circle cx="460" cy="190" r="5" />
            <circle cx="400" cy="130" r="3" className="chem-node-faint" />
            <circle cx="420" cy="260" r="4" />
            <circle cx="330" cy="210" r="3" className="chem-node-faint" />
          </g>
          <polygon className="chem-ring" points="620,58 654,78 654,118 620,138 586,118 586,78" />
          <polygon className="chem-ring chem-ring-small" points="440,272 460,284 460,308 440,320 420,308 420,284" />
          <path className="chem-orbit" d="M 560,60 C 640,20 730,80 685,160 C 662,202 600,192 578,142" />
          <path className="chem-dotted" d="M 320,240 C 400,196 460,262 540,232 C 582,216 622,232 654,202" />
        </svg>
      </div>
      <div className="hero-inner">
        <div className="hero-content">
          <h1>{t("home.hero.titlePrefix")}<em>{t("home.hero.titleEm")}</em></h1>
          <FormulaInput value={query} onChange={setQuery} onSubmit={() => query.trim() && navigate(`/analysis?formula=${encodeURIComponent(query.trim())}`)} />
        </div>
        <div className="hero-examples">
          <div className="section-heading">
            <div><p className="eyebrow">{t("home.quickStart.eyebrow")}</p><h2>{t("home.quickStart.title")}</h2></div>
            <a href="/examples">{t("home.quickStart.seeAll")}</a>
          </div>
          {examples.length ? <ExampleMoleculeGrid examples={examples} onSelect={select} /> : <p className="muted">{t("home.quickStart.empty")}</p>}
        </div>
      </div>
    </section></PageContainer>;
}
