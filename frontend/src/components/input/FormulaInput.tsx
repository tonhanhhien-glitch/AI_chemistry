import type { FormEvent } from "react";

export default function FormulaInput({ value, onChange, onSubmit, loading = false }: { value: string; onChange: (value: string) => void; onSubmit: () => void; loading?: boolean }) {
  function submit(event: FormEvent) { event.preventDefault(); onSubmit(); }
  return <form className="formula-form" onSubmit={submit}><label htmlFor="formula">Công thức hoặc tên chất</label><div className="search-row"><input id="formula" value={value} onChange={(event) => onChange(event.target.value)} maxLength={80} placeholder="Ví dụ: H2O, XeF4, NO3-" autoComplete="off" /><button disabled={loading}>{loading ? "Đang phân tích…" : "Phân tích"}</button></div><small>Chỉ hỗ trợ công thức phẳng; ngoặc, hệ số, hydrate và kim loại chuyển tiếp chưa được hỗ trợ.</small></form>;
}
