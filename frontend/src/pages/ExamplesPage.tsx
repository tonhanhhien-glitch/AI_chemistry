import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getExamples } from "../api/moleculeApi";
import ExampleMoleculeGrid from "../components/input/ExampleMoleculeGrid";
import PageContainer from "../components/layout/PageContainer";
import type { MoleculeSummary } from "../types/molecule";

export default function ExamplesPage() {
  const [examples, setExamples] = useState<MoleculeSummary[]>([]); const [error, setError] = useState(""); const navigate = useNavigate();
  useEffect(() => { void getExamples().then(setExamples).catch(() => setError("Không tải được ví dụ. Hãy kiểm tra backend.")); }, []);
  const groups = examples.reduce<Record<string, MoleculeSummary[]>>((acc, item) => { (acc[item.molecular_geometry_vi] ||= []).push(item); return acc; }, {});
  return <PageContainer><header className="page-intro"><p className="eyebrow">Thư viện tuyển chọn</p><h1>Ví dụ theo hình học</h1><p>Nhấn một chất để chạy toàn bộ quy trình phân tích offline.</p></header>{error && <p className="error-message">{error}</p>}{Object.entries(groups).map(([geometry, items]) => <section className="content-section" key={geometry}><h2>{geometry}</h2><ExampleMoleculeGrid examples={items} onSelect={(item) => navigate(`/analysis?id=${item.id}`)} /></section>)}</PageContainer>;
}
