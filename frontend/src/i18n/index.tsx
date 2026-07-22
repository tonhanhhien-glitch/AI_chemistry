// Lightweight i18n layer: a React context plus a module-level mirror so that
// non-React code (e.g. the axios client) can translate too. Defaults to
// Vietnamese so components render correctly even without a provider (tests).
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { DEFAULT_LANG, LANGUAGES, translate, type Lang } from "./translations";

export type { Lang } from "./translations";
export { LANGUAGES } from "./translations";

const STORAGE_KEY = "vsepr-lang";

// Module-level current language, kept in sync by the provider. Used by code that
// runs outside the React tree (see `t` below).
let activeLang: Lang = DEFAULT_LANG;

export function getLang(): Lang {
  return activeLang;
}

/** Translate using the currently active language. Safe to call outside React. */
export function t(key: string, params?: Record<string, string | number>): string {
  return translate(activeLang, key, params);
}

function readInitialLang(): Lang {
  if (typeof window === "undefined") return DEFAULT_LANG;
  const stored = window.localStorage.getItem(STORAGE_KEY);
  return (LANGUAGES as string[]).includes(stored || "") ? (stored as Lang) : DEFAULT_LANG;
}

interface I18nContextValue {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: (key: string, params?: Record<string, string | number>) => string;
}

const I18nContext = createContext<I18nContextValue>({
  lang: DEFAULT_LANG,
  setLang: () => undefined,
  t: (key, params) => translate(DEFAULT_LANG, key, params),
});

export function I18nProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(readInitialLang);

  const setLang = useCallback((next: Lang) => {
    activeLang = next;
    setLangState(next);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, next);
      document.documentElement.lang = next;
    }
  }, []);

  useEffect(() => {
    activeLang = lang;
    if (typeof document !== "undefined") document.documentElement.lang = lang;
  }, [lang]);

  const value = useMemo<I18nContextValue>(
    () => ({ lang, setLang, t: (key, params) => translate(lang, key, params) }),
    [lang, setLang],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  return useContext(I18nContext);
}
