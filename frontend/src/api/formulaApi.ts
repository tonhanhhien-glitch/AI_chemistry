import { apiClient } from "./client";

export interface FormulaParseResult {
  formula: string;
  atoms: Record<string, number>;
  charge: number;
}

export async function parseFormula(formula: string): Promise<FormulaParseResult> {
  const response = await apiClient.get<FormulaParseResult>("/formula", {
    params: { formula },
  });
  return response.data;
}
