import { useI18n } from "../../i18n";

export default function RatingWidget({ value, onChange }: { value: number; onChange: (value: number) => void }) {
  const { t } = useI18n();
  return <fieldset className="rating-widget"><legend>{t("feedback.rating.legend")}</legend>{[1, 2, 3, 4, 5].map((rating) => <label key={rating}><input type="radio" name="rating" checked={value === rating} onChange={() => onChange(rating)} /><span>{rating}</span></label>)}</fieldset>;
}
