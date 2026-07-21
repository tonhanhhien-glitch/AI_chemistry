export default function AtomLabelToggle({ checked, onChange }: { checked: boolean; onChange: (value: boolean) => void }) {
  return <label className="check-control"><input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} /> Nhãn nguyên tử</label>;
}
