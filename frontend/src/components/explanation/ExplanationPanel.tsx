import { useState } from "react";
import { useExplanation } from "../../hooks/useExplanation";
import type { Explanation, ExplanationLevel } from "../../types/explanation";
import AIDisclaimer from "./AIDisclaimer";
import ExplanationLevelSelector from "./ExplanationLevelSelector";
import ExplanationSection from "./ExplanationSection";

const titles: Record<string, string> = { lewis: "Cấu trúc Lewis", ax_en: "Phân loại AXnEm", electron_geometry: "Hình học miền electron", molecular_geometry: "Hình học phân tử", structure_property: "Liên hệ cấu trúc – tính chất", learning_tip: "Mẹo học", disclaimer: "Lưu ý" };

export default function ExplanationPanel({ moleculeId, initial }: { moleculeId: string; initial: Explanation | null }) {
  const { explanation, isLoading, error, regenerate } = useExplanation(initial); const [level, setLevel] = useState<ExplanationLevel>(initial?.level || "intermediate");
  if (!explanation) return <div><p>Chưa tạo giải thích. Nhấn nút để dùng dữ kiện đã kiểm tra.</p><ExplanationLevelSelector value={level} onChange={setLevel} /><button onClick={() => void regenerate(moleculeId, level)}>Tạo giải thích</button>{error && <p className="error-message">{error}</p>}</div>;
  return <div className="explanation-panel"><div className="explanation-actions"><ExplanationLevelSelector value={level} onChange={setLevel} disabled={isLoading} /><button onClick={() => void regenerate(moleculeId, level)} disabled={isLoading}>{isLoading ? "Đang tạo…" : "Tạo lại"}</button><button className="secondary-button" onClick={() => void navigator.clipboard?.writeText(Object.values(explanation.sections).join("\n\n"))}>Sao chép</button></div>{explanation.fallback_reason && <p className="offline-notice">{explanation.fallback_reason}</p>}{Object.entries(explanation.sections).map(([key, value]) => <ExplanationSection key={key} title={titles[key]}>{value}</ExplanationSection>)}<AIDisclaimer source={explanation.source} />{error && <p className="error-message">{error}</p>}</div>;
}
