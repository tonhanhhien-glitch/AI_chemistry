import { useEffect, useState } from "react";
import { searchMolecules } from "../api/moleculeApi";
import type { MoleculeSummary } from "../types/molecule";

export function useMoleculeSearch(query: string) {
  const [results, setResults] = useState<MoleculeSummary[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 2) {
      setResults([]);
      setIsLoading(false);
      return;
    }

    const controller = new AbortController();
    setIsLoading(true);

    const timer = window.setTimeout(() => {
      searchMolecules(trimmed, controller.signal)
        .then((data) => {
          setResults(data);
          setIsLoading(false);
        })
        .catch((err: unknown) => {
          if (err && typeof err === "object" && ("name" in err) && (err.name === "CanceledError" || err.name === "AbortError")) {
            return;
          }
          setResults([]);
          setIsLoading(false);
        });
    }, 200);

    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [query]);

  return { results, isLoading };
}
