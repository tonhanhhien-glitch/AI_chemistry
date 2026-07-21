import { useEffect, useState } from "react";
import { searchMolecules } from "../api/moleculeApi";
import type { MoleculeSummary } from "../types/molecule";

export function useMoleculeSearch(query: string) {
  const [results, setResults] = useState<MoleculeSummary[]>([]);
  useEffect(() => {
    if (query.trim().length < 2) { setResults([]); return; }
    const timer = window.setTimeout(() => { void searchMolecules(query).then(setResults).catch(() => setResults([])); }, 250);
    return () => window.clearTimeout(timer);
  }, [query]);
  return results;
}
