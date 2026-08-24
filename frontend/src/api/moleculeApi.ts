const API_URL = "http://127.0.0.1:8000";

export async function analyzeFormula(formula: string) {
  const response = await fetch(
    `${API_URL}/api/v1/analyze?formula=${encodeURIComponent(formula)}`
  );

  if (!response.ok) {
    throw new Error("Backend Error");
  }

  return response.json();
}