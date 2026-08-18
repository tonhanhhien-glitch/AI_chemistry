import { useState } from "react";
import { adminLogin } from "../../api/moleculeAdminApi";
import { getApiErrorMessage } from "../../api/client";
import { useI18n } from "../../i18n";

export default function AdminLogin({ onSuccess }: { onSuccess: (username: string) => void }) {
  const { t } = useI18n();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const status = await adminLogin(username, password);
      if (status.authenticated && status.username) onSuccess(status.username);
      else setError(t("moleculeData.login.error"));
    } catch (caught) {
      setError(getApiErrorMessage(caught) || t("moleculeData.login.error"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="admin-login-shell">
      <form className="admin-login-form formula-form" onSubmit={submit}>
        <h1>{t("moleculeData.login.title")}</h1>
        <p className="muted">{t("moleculeData.login.lede")}</p>
        <label htmlFor="admin-username">{t("moleculeData.login.username")}</label>
        <input
          id="admin-username"
          autoComplete="username"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          required
        />
        <label htmlFor="admin-password">{t("moleculeData.login.password")}</label>
        <input
          id="admin-password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
        />
        {error && <p className="admin-login-error" role="alert">{error}</p>}
        <button type="submit" disabled={loading}>
          {loading ? t("moleculeData.login.loading") : t("moleculeData.login.submit")}
        </button>
      </form>
    </div>
  );
}
