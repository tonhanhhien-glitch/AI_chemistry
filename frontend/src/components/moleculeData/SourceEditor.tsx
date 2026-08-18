import { useI18n } from "../../i18n";
import type { MoleculeDraft } from "../../types/moleculeAdmin";

const REVIEW_STATUS_SUGGESTIONS = ["draft", "internal_golden_pending_expert_signoff", "expert_verified"];

export default function SourceEditor({ draft, onChange }: { draft: MoleculeDraft; onChange: (patch: Partial<MoleculeDraft>) => void }) {
  const { t } = useI18n();
  const provenance = draft.review_provenance ?? {
    source_name: null, reference: null, url: null, evidence_type: null, conditions: null, retrieved_at: null,
  };

  function patchProvenance(field: keyof typeof provenance, value: string) {
    onChange({ review_provenance: { ...provenance, [field]: value || null } });
  }

  return (
    <div className="molecule-data-tab">
      <div className="molecule-data-tab-grid">
        <div className="molecule-data-field">
          <label htmlFor="source-status">{t("moleculeData.sourceReview.reviewStatus")}</label>
          <input id="source-status" list="review-status-options" value={draft.review_status}
            onChange={(event) => onChange({ review_status: event.target.value })} />
          <datalist id="review-status-options">
            {REVIEW_STATUS_SUGGESTIONS.map((status) => <option key={status} value={status} />)}
          </datalist>
        </div>
        <div className="molecule-data-field">
          <label htmlFor="source-confidence">{t("moleculeData.sourceReview.confidence")}</label>
          <select id="source-confidence" value={draft.confidence}
            onChange={(event) => onChange({ confidence: event.target.value as MoleculeDraft["confidence"] })}>
            <option value="high">high</option>
            <option value="medium">medium</option>
            <option value="low">low</option>
          </select>
        </div>
        <div className="molecule-data-field">
          <label htmlFor="source-kind">{t("moleculeData.sourceReview.source")}</label>
          <select id="source-kind" value={draft.source}
            onChange={(event) => onChange({ source: event.target.value as MoleculeDraft["source"] })}>
            <option value="curated">curated</option>
            <option value="deterministic">deterministic</option>
            <option value="PubChem reference">PubChem reference</option>
            <option value="cache">cache</option>
          </select>
        </div>
      </div>

      {draft.review_status === "expert_verified" && (
        <p className="admin-login-error">{t("moleculeData.sourceReview.expertVerifiedWarning")}</p>
      )}

      <h3>{t("moleculeData.sourceReview.provenanceTitle")}</h3>
      <div className="molecule-data-tab-grid">
        <div className="molecule-data-field">
          <label htmlFor="prov-name">{t("moleculeData.sourceReview.sourceName")}</label>
          <input id="prov-name" value={provenance.source_name ?? ""} onChange={(event) => patchProvenance("source_name", event.target.value)} />
        </div>
        <div className="molecule-data-field">
          <label htmlFor="prov-reference">{t("moleculeData.sourceReview.reference")}</label>
          <input id="prov-reference" value={provenance.reference ?? ""} onChange={(event) => patchProvenance("reference", event.target.value)} />
        </div>
        <div className="molecule-data-field molecule-data-field-wide">
          <label htmlFor="prov-url">{t("moleculeData.sourceReview.url")}</label>
          <input id="prov-url" value={provenance.url ?? ""} onChange={(event) => patchProvenance("url", event.target.value)} />
        </div>
        <div className="molecule-data-field">
          <label htmlFor="prov-evidence-type">{t("moleculeData.sourceReview.evidenceType")}</label>
          <input id="prov-evidence-type" value={provenance.evidence_type ?? ""} onChange={(event) => patchProvenance("evidence_type", event.target.value)} />
        </div>
        <div className="molecule-data-field">
          <label htmlFor="prov-conditions">{t("moleculeData.sourceReview.conditions")}</label>
          <input id="prov-conditions" value={provenance.conditions ?? ""} onChange={(event) => patchProvenance("conditions", event.target.value)} />
        </div>
        <div className="molecule-data-field">
          <label htmlFor="prov-retrieved">{t("moleculeData.sourceReview.retrievedAt")}</label>
          <input id="prov-retrieved" type="date" value={provenance.retrieved_at ? provenance.retrieved_at.slice(0, 10) : ""}
            onChange={(event) => patchProvenance("retrieved_at", event.target.value)} />
        </div>
      </div>
    </div>
  );
}
