import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getExamples } from "../api/moleculeApi";
import ExampleMoleculeGrid from "../components/input/ExampleMoleculeGrid";
import PageContainer from "../components/layout/PageContainer";
import { useI18n } from "../i18n";
import { geometryLabel } from "../utils/geometryLabels";
import type { MoleculeSummary } from "../types/molecule";

export default function ExamplesPage() {
  const { t } = useI18n();
  const [examples, setExamples] = useState<MoleculeSummary[]>([]); const [error, setError] = useState(""); const navigate = useNavigate();
  useEffect(() => { void getExamples().then(setExamples).catch(() => setError(t("examples.loadError"))); }, [t]);
  const groups = examples.reduce<Record<string, MoleculeSummary[]>>((acc, item) => { (acc[item.molecular_geometry] ||= []).push(item); return acc; }, {});
  return <PageContainer><header className="page-intro"><p className="eyebrow">{t("examples.eyebrow")}</p><h1>{t("examples.title")}</h1><p>{t("examples.intro")}</p></header>{error && <p className="error-message">{error}</p>}{Object.entries(groups).map(([geometry, items]) => <section className="content-section" key={geometry}><h2>{geometryLabel(t, geometry)}</h2><ExampleMoleculeGrid examples={items} onSelect={(item) => navigate(`/analysis?id=${item.id}`)} /></section>)}</PageContainer>;
}
