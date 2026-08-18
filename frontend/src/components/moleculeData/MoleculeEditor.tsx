import { useEffect, useRef, useState } from "react";
import { isAxiosError } from "axios";
import {
  createAdminMolecule, generateAdminDraft, getAdminMolecule, previewAdminMolecule,
  revertAdminMolecule, updateAdminMolecule, validateAdminMolecule,
} from "../../api/moleculeAdminApi";
import { getApiErrorMessage } from "../../api/client";
import { useI18n } from "../../i18n";
import type { AnalysisResult } from "../../types/analysis";
import type {
  MolecularGeometryEvidenceDraft, MoleculeDraft, ValidationReport,
} from "../../types/moleculeAdmin";
import type { NormalizedProperty } from "../../types/properties";
import { emptyMoleculeDraft } from "./defaults";
import IdentityEditor from "./IdentityEditor";
import LewisEditor from "./LewisEditor";
import VseprEditor from "./VseprEditor";
import GeometryEditor from "./GeometryEditor";
import PropertyEditor from "./PropertyEditor";
import TeachingEditor from "./TeachingEditor";
import SourceEditor from "./SourceEditor";
import ValidationPanel from "./ValidationPanel";
import PreviewPane from "./PreviewPane";

type TabKey = "identity" | "lewis" | "vsepr" | "geometry" | "properties" | "teaching" | "source";
const TABS: TabKey[] = ["identity", "lewis", "vsepr", "geometry", "properties", "teaching", "source"];

interface Snapshot { molecule: MoleculeDraft; geometry: MolecularGeometryEvidenceDraft | null; properties: NormalizedProperty[] }

export default function MoleculeEditor({
  moleculeId, onSaved, onRemoved,
}: { moleculeId: string | null; onSaved: (id: string) => void; onRemoved: () => void }) {
  const { t } = useI18n();
  const [loading, setLoading] = useState(true);
  const [draft, setDraft] = useState<MoleculeDraft>(emptyMoleculeDraft());
  const [geometry, setGeometry] = useState<MolecularGeometryEvidenceDraft | null>(null);
  const [properties, setProperties] = useState<NormalizedProperty[]>([]);
  const [activeTab, setActiveTab] = useState<TabKey>("identity");
  const [validation, setValidation] = useState<ValidationReport | null>(null);
  const [preview, setPreview] = useState<AnalysisResult | null>(null);
  const [busy, setBusy] = useState<"validate" | "preview" | "save" | "revert" | null>(null);
  const [autoCalculating, setAutoCalculating] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const snapshotRef = useRef<string>("");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setActionError(null);
    setValidation(null);
    setPreview(null);
    setSavedAt(null);
    setActiveTab("identity");
    if (moleculeId) {
      getAdminMolecule(moleculeId).then((record) => {
        if (cancelled) return;
        setDraft(record.molecule);
        setGeometry(record.experimental_geometry);
        setProperties(record.properties);
        snapshotRef.current = JSON.stringify({ molecule: record.molecule, geometry: record.experimental_geometry, properties: record.properties });
      }).catch((error: unknown) => { if (!cancelled) setActionError(getApiErrorMessage(error)); })
        .finally(() => { if (!cancelled) setLoading(false); });
    } else {
      const blank = emptyMoleculeDraft();
      setDraft(blank);
      setGeometry(null);
      setProperties([]);
      snapshotRef.current = JSON.stringify({ molecule: blank, geometry: null, properties: [] } satisfies Snapshot);
      setLoading(false);
    }
    return () => { cancelled = true; };
  }, [moleculeId]);

  const currentSnapshot = JSON.stringify({ molecule: draft, geometry, properties } satisfies Snapshot);
  const dirty = currentSnapshot !== snapshotRef.current;

  function updateDraft(patch: Partial<MoleculeDraft>) {
    setDraft((prev) => ({ ...prev, ...patch }));
  }

  async function handleAutoCalculate() {
    if (!draft.formula) return;
    setAutoCalculating(true);
    setActionError(null);
    try {
      const generated = await generateAdminDraft(draft.formula, draft.charge, draft.id || undefined);
      setDraft((prev) => ({ ...prev, ...generated, id: prev.id || generated.id }));
    } catch (error) {
      setActionError(getApiErrorMessage(error));
    } finally {
      setAutoCalculating(false);
    }
  }

  async function handleValidate() {
    setBusy("validate");
    setActionError(null);
    try {
      const report = await validateAdminMolecule(draft.id || "draft", { molecule: draft, experimental_geometry: geometry, properties });
      setValidation(report);
    } catch (error) {
      setActionError(getApiErrorMessage(error));
    } finally {
      setBusy(null);
    }
  }

  async function handlePreview() {
    setBusy("preview");
    setActionError(null);
    try {
      const result = await previewAdminMolecule({ molecule: draft, experimental_geometry: geometry, properties });
      setPreview(result);
    } catch (error) {
      setActionError(getApiErrorMessage(error));
    } finally {
      setBusy(null);
    }
  }

  async function handleSave() {
    setBusy("save");
    setActionError(null);
    try {
      const payload = { molecule: draft, experimental_geometry: geometry, properties };
      const response = moleculeId ? await updateAdminMolecule(draft.id, payload) : await createAdminMolecule(payload);
      setValidation(response.validation);
      setSavedAt(response.saved_at);
      snapshotRef.current = currentSnapshot;
      onSaved(response.molecule.id);
    } catch (error) {
      setActionError(getApiErrorMessage(error));
      if (isAxiosError(error) && error.response?.status === 422 && error.response.data?.detail?.errors) {
        setValidation(error.response.data.detail as ValidationReport);
      }
    } finally {
      setBusy(null);
    }
  }

  function handleDiscard() {
    if (!dirty) return;
    if (!window.confirm(t("moleculeData.confirm.discard"))) return;
    const snapshot = JSON.parse(snapshotRef.current) as Snapshot;
    setDraft(snapshot.molecule);
    setGeometry(snapshot.geometry);
    setProperties(snapshot.properties);
    setValidation(null);
    setPreview(null);
  }

  async function handleRevert() {
    if (!moleculeId) return;
    if (!window.confirm(t("moleculeData.confirm.revert"))) return;
    setBusy("revert");
    setActionError(null);
    try {
      const result = await revertAdminMolecule(moleculeId);
      if (!result.reverted_to_baseline) {
        onRemoved();
        return;
      }
      const record = await getAdminMolecule(moleculeId);
      setDraft(record.molecule);
      setGeometry(record.experimental_geometry);
      setProperties(record.properties);
      snapshotRef.current = JSON.stringify({ molecule: record.molecule, geometry: record.experimental_geometry, properties: record.properties } satisfies Snapshot);
      setValidation(null);
      setPreview(null);
      onSaved(record.molecule.id);
    } catch (error) {
      setActionError(getApiErrorMessage(error));
    } finally {
      setBusy(null);
    }
  }

  if (loading) return <p className="muted">{t("moleculeData.editor.loading")}</p>;

  return (
    <div className="molecule-data-editor">
      <div className="molecule-data-editor-header">
        <h2>{draft.formula || t("moleculeData.editor.newMolecule")}</h2>
        <span className={dirty ? "molecule-data-status dirty" : "molecule-data-status clean"}>
          {dirty ? t("moleculeData.editor.unsaved") : savedAt ? t("moleculeData.editor.saved") : ""}
        </span>
      </div>

      <div className="molecule-data-tabs" role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            role="tab"
            aria-selected={activeTab === tab}
            className={activeTab === tab ? "molecule-data-tab-button active" : "molecule-data-tab-button"}
            onClick={() => setActiveTab(tab)}
          >
            {t(`moleculeData.tabs.${tab}`)}
          </button>
        ))}
      </div>

      {activeTab === "identity" && <IdentityEditor draft={draft} onChange={updateDraft} isNew={!moleculeId} />}
      {activeTab === "lewis" && (
        <LewisEditor draft={draft} onChange={updateDraft} onAutoCalculate={handleAutoCalculate} onValidate={handleValidate} autoCalculating={autoCalculating} />
      )}
      {activeTab === "vsepr" && (
        <VseprEditor draft={draft} onChange={updateDraft} onAutoCalculate={handleAutoCalculate} onValidate={handleValidate} autoCalculating={autoCalculating} />
      )}
      {activeTab === "geometry" && <GeometryEditor geometry={geometry} onChange={setGeometry} draft={draft} />}
      {activeTab === "properties" && <PropertyEditor properties={properties} onChange={setProperties} />}
      {activeTab === "teaching" && <TeachingEditor draft={draft} onChange={updateDraft} />}
      {activeTab === "source" && <SourceEditor draft={draft} onChange={updateDraft} />}

      <div className="molecule-data-action-bar">
        <button type="button" onClick={handleValidate} disabled={busy !== null}>
          {busy === "validate" ? t("moleculeData.actions.validating") : t("moleculeData.actions.validate")}
        </button>
        <button type="button" onClick={handlePreview} disabled={busy !== null}>
          {busy === "preview" ? t("moleculeData.actions.previewing") : t("moleculeData.actions.preview")}
        </button>
        <button type="button" onClick={handleSave} disabled={busy !== null}>
          {busy === "save" ? t("moleculeData.actions.saving") : t("moleculeData.actions.save")}
        </button>
        <button type="button" onClick={handleDiscard} disabled={busy !== null || !dirty}>
          {t("moleculeData.actions.discard")}
        </button>
        {moleculeId && (
          <button type="button" onClick={handleRevert} disabled={busy !== null}>
            {busy === "revert" ? t("moleculeData.actions.reverting") : t("moleculeData.actions.revert")}
          </button>
        )}
        {savedAt && <span className="muted molecule-data-saved-at">{t("moleculeData.editor.lastSaved", { time: new Date(savedAt).toLocaleString() })}</span>}
      </div>

      {actionError && <p className="admin-login-error" role="alert">{actionError}</p>}
      <ValidationPanel report={validation} />
      <PreviewPane preview={preview} />
    </div>
  );
}
