import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";

import { getApiErrorMessage } from "../api/client";
import {
  FormulaParseResult,
  parseFormula,
} from "../api/formulaApi";

export default function AnalysisPage() {
  const [formula, setFormula] = useState("");
  const [result, setResult] = useState<FormulaParseResult | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);

    if (!formula.trim()) {
      setError("Vui lòng nhập công thức hóa học.");
      return;
    }

    setIsLoading(true);
    try {
      setResult(await parseFormula(formula));
    } catch (requestError) {
      setError(getApiErrorMessage(requestError));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="page">
      <nav className="top-nav" aria-label="Điều hướng chính">
        <Link to="/">VSEPR-AI</Link>
        <span>Phân tích công thức</span>
      </nav>

      <section className="analysis-layout">
        <div className="card input-card">
          <p className="eyebrow">Bước đầu tiên</p>
          <h1>Nhập công thức</h1>
          <p>
            Hỗ trợ công thức phẳng như NaCl, XeF4 và ion đơn giản như SO4^2-.
          </p>

          <form onSubmit={handleSubmit}>
            <label htmlFor="formula">Công thức hóa học</label>
            <div className="form-row">
              <input
                id="formula"
                name="formula"
                value={formula}
                onChange={(event) => setFormula(event.target.value)}
                placeholder="Ví dụ: NaCl"
                autoComplete="off"
                aria-describedby={error ? "formula-error" : undefined}
              />
              <button type="submit" disabled={isLoading}>
                {isLoading ? "Đang phân tích…" : "Phân tích"}
              </button>
            </div>
          </form>

          {error && (
            <p className="error-message" id="formula-error" role="alert">
              {error}
            </p>
          )}
        </div>

        <div className="card result-card" aria-live="polite">
          <p className="eyebrow">Kết quả</p>
          {!result && !isLoading && (
            <p className="empty-state">Kết quả sẽ xuất hiện tại đây.</p>
          )}
          {isLoading && <p className="empty-state">Đang gửi yêu cầu…</p>}
          {result && (
            <>
              <dl className="summary">
                <div>
                  <dt>Công thức</dt>
                  <dd>{result.formula}</dd>
                </div>
                <div>
                  <dt>Điện tích</dt>
                  <dd>{result.charge > 0 ? `+${result.charge}` : result.charge}</dd>
                </div>
              </dl>
              <table>
                <thead>
                  <tr>
                    <th>Nguyên tố</th>
                    <th>Số lượng</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(result.atoms).map(([element, count]) => (
                    <tr key={element}>
                      <td>{element}</td>
                      <td>{count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </div>
      </section>
    </main>
  );
}
