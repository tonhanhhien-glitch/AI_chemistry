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
  return <PageContainer><section className="hero-grid"><div><p className="eyebrow">{t("home.hero.eyebrow")}</p><h1>{t("home.hero.titlePrefix")}<em>{t("home.hero.titleEm")}</em></h1><p className="lede">{t("home.hero.lede")}</p><FormulaInput value={query} onChange={setQuery} onSubmit={() => query.trim() && navigate(`/analysis?formula=${encodeURIComponent(query.trim())}`)} /></div><div className="hero-visual" aria-label={t("home.hero.visualAria")}><span className="orb orb-a">O</span><span className="bond-line" /><span className="orb orb-c">C</span><span className="bond-line second" /><span className="orb orb-b">O</span><p>CO₂ · AX2 · 180°</p></div></section><section className="trust-strip"><div><strong>100%</strong><span>{t("home.trust.offline")}</span></div><div><strong>13</strong><span>{t("home.trust.axTypes")}</span></div><div><strong>0</strong><span>{t("home.trust.noLlm")}</span></div></section><section className="content-section"><div className="section-heading"><div><p className="eyebrow">{t("home.quickStart.eyebrow")}</p><h2>{t("home.quickStart.title")}</h2></div><a href="/examples">{t("home.quickStart.seeAll")}</a></div>{examples.length ? <ExampleMoleculeGrid examples={examples} onSelect={select} /> : <p className="muted">{t("home.quickStart.empty")}</p>}</section><section className="scope-card"><h2>{t("home.scope.title")}</h2><p>{t("home.scope.body")}</p></section></PageContainer>;
}
