import { useState } from "react";
import { useI18n } from "../../i18n";
import { useFeedback } from "../../hooks/useFeedback";
import RatingWidget from "./RatingWidget";

export default function FeedbackForm({ moleculeId }: { moleculeId: string }) {
  const { t } = useI18n();
  const [rating, setRating] = useState(5); const [comment, setComment] = useState(""); const [category, setCategory] = useState<"clarity" | "usefulness" | "chemistry_error" | "other">("usefulness"); const { submit, status, isLoading } = useFeedback();
  return <form className="feedback-form" onSubmit={(event) => { event.preventDefault(); void submit({ session_id: localStorage.getItem("vsepr-session") || undefined, molecule_id: moleculeId, rating, category, comment: comment || undefined }); }}><RatingWidget value={rating} onChange={setRating} /><label>{t("feedback.categoryLabel")}<select value={category} onChange={(event) => setCategory(event.target.value as typeof category)}><option value="usefulness">{t("feedback.category.usefulness")}</option><option value="clarity">{t("feedback.category.clarity")}</option><option value="chemistry_error">{t("feedback.category.chemistryError")}</option><option value="other">{t("feedback.category.other")}</option></select></label><label>{t("feedback.commentLabel")}<textarea value={comment} onChange={(event) => setComment(event.target.value)} maxLength={1000} /></label><button disabled={isLoading}>{isLoading ? t("feedback.submitting") : t("feedback.submit")}</button>{status && <p role="status">{status}</p>}</form>;
}
