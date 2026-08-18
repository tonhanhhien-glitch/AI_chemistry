import { useEffect, useState } from "react";
import { adminLogout, adminSession } from "../api/moleculeAdminApi";
import AdminLogin from "../components/moleculeData/AdminLogin";
import MoleculeEditor from "../components/moleculeData/MoleculeEditor";
import MoleculeList from "../components/moleculeData/MoleculeList";
import PageContainer from "../components/layout/PageContainer";
import { useI18n } from "../i18n";

type Selection = { kind: "none" } | { kind: "existing"; id: string } | { kind: "new" };

export default function MoleculeDataPage() {
  const { t } = useI18n();
  const [authChecked, setAuthChecked] = useState(false);
  const [authenticated, setAuthenticated] = useState(false);
  const [username, setUsername] = useState<string | null>(null);
  const [selection, setSelection] = useState<Selection>({ kind: "none" });
  const [refreshToken, setRefreshToken] = useState(0);

  useEffect(() => {
    let cancelled = false;
    adminSession()
      .then((status) => {
        if (cancelled) return;
        setAuthenticated(status.authenticated);
        setUsername(status.username);
      })
      .finally(() => { if (!cancelled) setAuthChecked(true); });
    return () => { cancelled = true; };
  }, []);

  async function handleLogout() {
    await adminLogout();
    setAuthenticated(false);
    setUsername(null);
    setSelection({ kind: "none" });
  }

  if (!authChecked) {
    return <PageContainer className="molecule-data-shell"><p className="muted">{t("moleculeData.editor.loading")}</p></PageContainer>;
  }

  if (!authenticated) {
    return (
      <PageContainer className="molecule-data-shell">
        <AdminLogin onSuccess={(name) => { setAuthenticated(true); setUsername(name); }} />
      </PageContainer>
    );
  }

  return (
    <PageContainer className="molecule-data-shell">
      <div className="molecule-data-header">
        <h1>{t("moleculeData.title")}</h1>
        <div className="molecule-data-header-actions">
          {username && <span className="muted">{username}</span>}
          <button type="button" onClick={handleLogout}>{t("moleculeData.logout")}</button>
        </div>
      </div>
      <div className="molecule-data-layout">
        <MoleculeList
          selectedId={selection.kind === "existing" ? selection.id : null}
          onSelect={(id) => setSelection({ kind: "existing", id })}
          onAdd={() => setSelection({ kind: "new" })}
          refreshToken={refreshToken}
        />
        {selection.kind === "none" && <p className="muted molecule-data-placeholder">{t("moleculeData.editor.selectHint")}</p>}
        {selection.kind !== "none" && (
          <MoleculeEditor
            moleculeId={selection.kind === "existing" ? selection.id : null}
            onSaved={(id) => { setSelection({ kind: "existing", id }); setRefreshToken((value) => value + 1); }}
            onRemoved={() => { setSelection({ kind: "none" }); setRefreshToken((value) => value + 1); }}
          />
        )}
      </div>
    </PageContainer>
  );
}
