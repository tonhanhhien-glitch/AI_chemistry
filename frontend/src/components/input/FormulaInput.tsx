import { useState, useRef, useEffect, type FormEvent, type KeyboardEvent } from "react";
import { useI18n } from "../../i18n";
import { useMoleculeSearch } from "../../hooks/useMoleculeSearch";
import { ChemFormula } from "../../utils/chemFormula";
import { geometryLabel } from "../../utils/geometryLabels";
import type { MoleculeSummary } from "../../types/molecule";

interface FormulaInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (selected?: MoleculeSummary) => void;
  onSelectMolecule?: (molecule: MoleculeSummary) => void;
  loading?: boolean;
}

export default function FormulaInput({
  value,
  onChange,
  onSubmit,
  onSelectMolecule,
  loading = false,
}: FormulaInputProps) {
  const { t, lang } = useI18n();
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const { results, isLoading: isSearching } = useMoleculeSearch(value);

  useEffect(() => {
    if (results.length > 0) {
      setIsOpen(true);
      setSelectedIndex(-1);
    } else {
      setIsOpen(false);
    }
  }, [results]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleSelect(item: MoleculeSummary) {
    setIsOpen(false);
    if (onSelectMolecule) {
      onSelectMolecule(item);
    } else {
      onChange(item.formula);
      onSubmit(item);
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (!isOpen || results.length === 0) {
      if (e.key === "Enter") {
        e.preventDefault();
        onSubmit();
      }
      return;
    }

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % results.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev <= 0 ? results.length - 1 : prev - 1));
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (selectedIndex >= 0 && selectedIndex < results.length) {
        handleSelect(results[selectedIndex]);
      } else {
        setIsOpen(false);
        onSubmit();
      }
    } else if (e.key === "Escape") {
      setIsOpen(false);
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    setIsOpen(false);
    onSubmit();
  }

  return (
    <form className="formula-form" onSubmit={submit}>
      <label htmlFor="formula">{t("formulaInput.label")}</label>
      <div className="formula-input-container" ref={containerRef}>
        <div className="search-row">
          <input
            id="formula"
            ref={inputRef}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onFocus={() => {
              if (results.length > 0) setIsOpen(true);
            }}
            onKeyDown={handleKeyDown}
            maxLength={80}
            placeholder={t("formulaInput.placeholder")}
            autoComplete="off"
            role="combobox"
            aria-expanded={isOpen}
            aria-autocomplete="list"
          />
          <button type="submit" disabled={loading}>
            {loading ? t("formulaInput.analyzing") : t("formulaInput.analyze")}
          </button>
        </div>

        {isOpen && results.length > 0 && (
          <ul className="autocomplete-dropdown" role="listbox">
            {results.map((item, index) => {
              const name = lang === "vi" ? item.name_vi || item.name_en : item.name_en || item.name_vi;
              const shape = geometryLabel(t, item.molecular_geometry);
              const isSelected = index === selectedIndex;
              return (
                <li key={item.id} role="option" aria-selected={isSelected}>
                  <button
                    type="button"
                    className={`autocomplete-item ${isSelected ? "active" : ""}`}
                    onClick={() => handleSelect(item)}
                    onMouseEnter={() => setSelectedIndex(index)}
                  >
                    <div className="autocomplete-formula">
                      <ChemFormula text={item.formula} />
                    </div>
                    {name && <span className="autocomplete-name">{name}</span>}
                    {(item.ax_en || shape) && (
                      <small className="autocomplete-badge">
                        {item.ax_en && <ChemFormula text={item.ax_en} />}
                        {item.ax_en && shape && " · "}
                        {shape}
                      </small>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
      <small>{t("formulaInput.help")}</small>
    </form>
  );
}
