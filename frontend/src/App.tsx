import { useState } from "react";

import { analyzeFormula } from "./api/moleculeApi";

import Header from "./components/Header";
import FormulaInput from "./components/FormulaInput";
import InfoCard from "./components/InfoCard";
import LewisCard from "./components/LewisCard";
import ExplanationCard from "./components/ExplanationCard";
// import MoleculeViewer from "./components/MoleculeViewer";

export default function App() {
  const [formula, setFormula] = useState("H2O");
  const [result, setResult] = useState<any>(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [animate, setAnimate] = useState(false);
  const [showDomains, setShowDomains] = useState(true);

  async function handleAnalyze() {
    if (!formula.trim()) return;

    try {
      setLoading(true);
      setError("");

      const data = await analyzeFormula(formula.trim());

      setResult(data);
      setAnimate(false);
    } catch (err) {
      console.error(err);
      setError("Không thể phân tích phân tử.");
    } finally {
      setLoading(false);
    }
  }

  async function quickAnalyze(f: string) {
    setFormula(f);

    try {
      setLoading(true);
      setError("");

      const data = await analyzeFormula(f);

      setResult(data);
      setAnimate(false);
    } catch (err) {
      console.error(err);
      setError("Không thể phân tích phân tử.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        background: "#EEF3EF",
        minHeight: "100vh",
        padding: 40,
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

        {error && (
          <div
            style={{
              background: "#FFECEC",
              color: "#C62828",
              padding: 12,
              borderRadius: 12,
              marginBottom: 20,
            }}
          >
            {error}
          </div>
        )}

        {result && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 520px",
              gap: 24,
            }}
          >
            {/* LEFT */}
            <div>
              <InfoCard result={result} />

              <LewisCard result={result} />

              <ExplanationCard result={result} />
            </div>

            {/* RIGHT */}
            <div
              style={{
                background: "white",
                borderRadius: 18,
                overflow: "hidden",
                padding: 18,
                boxShadow: "0 6px 18px rgba(0,0,0,.08)",
              }}
            >
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: 12,
                }}
              >
                <h3
                  style={{
                    margin: 0,
                    color: "#0F2F28",
                  }}
                >
                  3D Molecule
                </h3>

                <button
                  onClick={() => setAnimate(!animate)}
                  style={{
                    background: animate ? "#147A5A" : "#EEF3EF",
                    color: animate ? "white" : "#147A5A",
                    border: "none",
                    borderRadius: 999,
                    padding: "8px 16px",
                    cursor: "pointer",
                    fontWeight: 700,
                  }}
                >
                  {animate ? "Pause" : "Play"}
                </button>
              </div>

              <label
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 8,
                  marginBottom: 12,
                  cursor: "pointer",
                }}
              >
                <input
                  type="checkbox"
                  checked={showDomains}
                  onChange={() =>
                    setShowDomains(!showDomains)
                  }
                />
                Electron Domains
              </label>

              <div
                style={{
                  width: "100%",
                  height: 420,
                  borderRadius: 14,
                  overflow: "hidden",
                  border: "1px solid #E3E7E5",
                }}
              >
                <div
                  style={{
                    width: "100%",
                    height: "420px",
                    display: "grid",
                    placeItems: "center",
                    background: "#F6F8F7",
                    color: "#147A5A",
                    borderRadius: 14,
                    border: "1px solid #E3E7E5",
                    fontWeight: 700,
                  }}
                >
                  3D Viewer tạm thời tắt để sửa
                </div>
              </div>

              <div
                style={{
                  marginTop: 14,
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 10,
                }}
              >
                <div
                  style={{
                    background: "#F6F8F7",
                    borderRadius: 12,
                    padding: 12,
                  }}
                >
                  <div
                    style={{
                      fontSize: 12,
                      color: "#666",
                    }}
                  >
                    Electron Geometry
                  </div>

                  <strong>
                    {result.data.vsepr?.electron_geometry ??
                      "-"}
                  </strong>
                </div>

                <div
                  style={{
                    background: "#F6F8F7",
                    borderRadius: 12,
                    padding: 12,
                  }}
                >
                  <div
                    style={{
                      fontSize: 12,
                      color: "#666",
                    }}
                  >
                    Molecular Geometry
                  </div>

                  <strong>
                    {result.data.vsepr?.molecular_geometry ??
                      "-"}
                  </strong>
                </div>

                <div
                  style={{
                    background: "#F6F8F7",
                    borderRadius: 12,
                    padding: 12,
                  }}
                >
                  <div
                    style={{
                      fontSize: 12,
                      color: "#666",
                    }}
                  >
                    Bond Angle
                  </div>

                  <strong>
                    {result.data.vsepr?.bond_angle ?? "-"}°
                  </strong>
                </div>

                <div
                  style={{
                    background: "#F6F8F7",
                    borderRadius: 12,
                    padding: 12,
                  }}
                >
                  <div
                    style={{
                      fontSize: 12,
                      color: "#666",
                    }}
                  >
                    AXE Model
                  </div>

                  <strong>
                    AX
                    {result.data.vsepr?.bonding_pairs ?? 0}
                    E
                    {result.data.vsepr?.lone_pairs ?? 0}
                  </strong>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}