export type ViewerStyle = "stick" | "sphere";

export default function StyleSelector({ value, onChange }: { value: ViewerStyle; onChange: (value: ViewerStyle) => void }) {
  return <label className="inline-control">Kiểu hiển thị<select value={value} onChange={(event) => onChange(event.target.value as ViewerStyle)}><option value="stick">Cầu và que</option><option value="sphere">Lấp đầy không gian</option></select></label>;
}
