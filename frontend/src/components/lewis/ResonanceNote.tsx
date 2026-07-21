export default function ResonanceNote({ forms, note }: { forms: number; note: string | null }) {
  if (forms <= 1 && !note) return null;
  return <aside className="callout"><strong>↔ {forms} công thức cộng hưởng tương đương</strong><p>{note}</p></aside>;
}
