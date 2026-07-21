export default function RatingWidget({ value, onChange }: { value: number; onChange: (value: number) => void }) {
  return <fieldset className="rating-widget"><legend>Mức hữu ích (1–5)</legend>{[1, 2, 3, 4, 5].map((rating) => <label key={rating}><input type="radio" name="rating" checked={value === rating} onChange={() => onChange(rating)} /><span>{rating}</span></label>)}</fieldset>;
}
