const API = "http://127.0.0.1:8000";

export async function analyzeFormula(formula: string) {
  const res = await fetch(
    `${API}/api/v1/analyze?formula=${encodeURIComponent(formula)}`
  );

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }

  return await res.json();
}