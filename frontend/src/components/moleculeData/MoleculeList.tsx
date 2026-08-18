import { useEffect, useState } from "react";
import { listAdminMolecules } from "../../api/moleculeAdminApi";
import { useI18n } from "../../i18n";
import { ChemFormula } from "../../utils/chemFormula";
import type { MoleculeAdminListItem } from "../../types/moleculeAdmin";

export default function MoleculeList({
  selectedId,
  onSelect,
  onAdd,
  refreshToken,
}: {
  selectedId: string | null;
  onSelect: (id: string) => void;
  onAdd: () => void;
  refreshToken: number;
}) {
  const { t, lang } = useI18n();
  const [query, setQuery] = useState("");
  const [items, setItems] = useState<MoleculeAdminListItem[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    listAdminMolecules(query.trim() || undefined)
      .then((results) => { if (!cancelled) setItems(results); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [query, refreshToken]);

  return (
    <div className="molecule-data-list">
      <label htmlFor="molecule-data-search">{t("moleculeData.list.search")}</label>
      <input
        id="molecule-data-search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder={t("moleculeData.list.searchPlaceholder")}
      />
      <ul className="molecule-data-list-items">
        {items.map((item) => {
          const name = lang === "vi" ? item.name_vi || item.name_en : item.name_en || item.name_vi;
          return (
            <li key={item.id}>
              <button
                type="button"
                className={item.id === selectedId ? "molecule-data-list-item active" : "molecule-data-list-item"}
                onClick={() => onSelect(item.id)}
              >
                <span className="molecule-data-list-formula"><ChemFormula text={item.formula} /></span>
                <span className="molecule-data-list-name">{name}</span>
                {item.has_override && (
                  <span className="molecule-data-badge">
                    {item.is_admin_added ? t("moleculeData.list.added") : t("moleculeData.list.edited")}
                  </span>
                )}
              </button>
            </li>
          );
        })}
        {!loading && items.length === 0 && <li className="muted">{t("moleculeData.list.empty")}</li>}
      </ul>
      <button type="button" className="molecule-data-add" onClick={onAdd}>
        {t("moleculeData.list.add")}
      </button>
    </div>
  );
}
