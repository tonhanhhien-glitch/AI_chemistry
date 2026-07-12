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
      setError("Please enter a chemical formula.");
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
      <nav className="top-nav" aria-label="Main navigation">
        <Link to="/">VSEPR-AI</Link>
        <span>Formula analysis</span>
      </nav>

      <section className="analysis-layout">
        <div className="card input-card">
          <p className="eyebrow">First step</p>
          <h1>Enter a formula</h1>
          <p>
            Supports flat formulas such as NaCl and XeF4, and simple ions such as SO4^2-.
          </p>

          <form onSubmit={handleSubmit}>
            <label htmlFor="formula">Chemical formula</label>
            <div className="form-row">
              <input
                id="formula"
                name="formula"
                value={formula}
                onChange={(event) => setFormula(event.target.value)}
                placeholder="Example: NaCl"
                autoComplete="off"
                aria-describedby={error ? "formula-error" : undefined}
              />
              <button type="submit" disabled={isLoading}>
                {isLoading ? "Analyzing…" : "Analyze"}
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
          <p className="eyebrow">Result</p>
          {!result && !isLoading && (
            <p className="empty-state">The result will appear here.</p>
          )}
          {isLoading && <p className="empty-state">Sending request…</p>}
          {result && (
            <>
              <dl className="summary">
                <div>
                  <dt>Formula</dt>
                  <dd>{result.formula}</dd>
                </div>
                <div>
                  <dt>Charge</dt>
                  <dd>{result.charge > 0 ? `+${result.charge}` : result.charge}</dd>
                </div>
              </dl>
              <table>
                <thead>
                  <tr>
                    <th>Element</th>
                    <th>Count</th>
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
