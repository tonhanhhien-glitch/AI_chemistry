import { useState, useEffect } from "react";

import { analyzeFormula } from "./api/moleculeApi";

import Header from "./components/Header";
import FormulaInput from "./components/FormulaInput";
import InfoCard from "./components/InfoCard";
import LewisCard from "./components/LewisCard";
import ExplanationCard from "./components/ExplanationCard";
import MoleculeViewer from "./components/MoleculeViewer";

export default function App() {
  const [formula, setFormula] = useState("H2O");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [isMobile, setIsMobile] = useState(window.innerWidth < 900);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 900);

    window.addEventListener("resize", handleResize);

    return () => window.removeEventListener("resize", handleResize);
  }, []);

  async function handleAnalyze(selectedFormula?: string) {
    const target = selectedFormula ?? formula;

    setLoading(true);
    setError("");

    try {
      const data = await analyzeFormula(target);

      setFormula(target);
      setResult(data);
    } catch (err) {
      console.error(err);
      setError("Không thể kết nối tới backend hoặc công thức không hợp lệ.");
    } finally {
      setLoading(false);
    }
  }

  const examples = ["H2O", "CO2", "NH3", "CH4", "BF3", "PCl5", "SF6"];

  return (
    <div
      style={{
        background: "#EEF3EF",
        minHeight: "100vh",
        padding: isMobile ? 20 : 40,
        fontFamily: "system-ui",
      }}
    >
      <div
        style={{
          maxWidth: 1200,
          margin: "0 auto",
        }}
      >
        <Header />

        <FormulaInput
          formula={formula}
          loading={loading}
          onChange={setFormula}
          onAnalyze={handleAnalyze}
        />

        {/* Quick Examples */}

        <div
          style={{
            display: "flex",
            gap: 10,
            flexWrap: "wrap",
            marginBottom: 28,
          }}
        >
          {examples.map((item) => (
            <button
              key={item}
              onClick={() => handleAnalyze(item)}
              disabled={loading}
              style={{
                padding: "8px 14px",
                borderRadius: 999,
                border: "1px solid #D7E3DD",
                background: "white",
                cursor: "pointer",
                fontWeight: 500,
              }}
            >
              {item}
            </button>
          ))}
        </div>

        {error && (
          <div
            style={{
              background: "#FDECEC",
              border: "1px solid #F5B7B7",
              color: "#B3261E",
              padding: 16,
              borderRadius: 14,
              marginBottom: 24,
            }}
          >
            {error}
          </div>
        )}

        {/* Empty State */}

        {!result && !loading && (
          <div
            style={{
              background: "white",
              borderRadius: 18,
              padding: 50,
              textAlign: "center",
              border: "1px dashed #C7D5CF",
            }}
          >
            <h2 style={{ color: "#0F2F28" }}>🧪 Bắt đầu phân tích</h2>

            <p
              style={{
                marginTop: 12,
                color: "#667085",
              }}
            >
              Nhập một công thức hóa học hoặc chọn một ví dụ phía trên rồi nhấn Analyze.
            </p>
          </div>
        )}

        {/* Loading */}

        {loading && (
          <div
            style={{
              background: "white",
              borderRadius: 18,
              padding: 50,
              textAlign: "center",
              border: "1px solid #DDD",
            }}
          >
            <div
              style={{
                width: 40,
                height: 40,
                border: "4px solid #D7E3DD",
                borderTopColor: "#147A5A",
                borderRadius: "50%",
                margin: "0 auto 18px",
                animation: "spin 1s linear infinite",
              }}
            />

            <h3 style={{ color: "#0F2F28" }}>Analyzing Molecule...</h3>

            <p style={{ color: "#667085" }}>
              Đang xây dựng Lewis Structure và tính toán VSEPR.
            </p>
          </div>
        )}

        {/* Result */}

        {result && !loading && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: isMobile ? "1fr" : "1fr 520px",
              gap: 24,
            }}
          >
            <div>
              <InfoCard result={result} />

              <LewisCard result={result} />

              <ExplanationCard result={result} />
            </div>

            <div
              style={{
                background: "white",
                borderRadius: 18,
                overflow: "hidden",
                height: 500,
                border: "1px solid #DDD",
                boxShadow: "0 8px 20px rgba(0,0,0,.05)",
              }}
            >
              <MoleculeViewer
                coordinates={result.data.coordinates}
                atoms={result.data.lewis.atom_objects}
              />
            </div>
          </div>
        )}
      </div>

      {/* Spinner animation */}

      <style>{`
        @keyframes spin{
          from{transform:rotate(0deg);}
          to{transform:rotate(360deg);}
        }
      `}</style>
    </div>
  );
}