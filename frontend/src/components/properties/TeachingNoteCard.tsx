export default function TeachingNoteCard({ note }: { note: string }) {
  return <aside className="teaching-note"><span aria-hidden="true">✦</span><div><strong>Mẹo học</strong><p>{note}</p></div></aside>;
}
