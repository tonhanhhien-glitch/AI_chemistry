const steps = ["Nhập chất", "Lewis", "AXnEm", "Hình học", "Mô hình 3D", "Giải thích"];

export default function WorkflowStepper({ active = 6 }: { active?: number }) {
  return <ol className="stepper" aria-label="Quy trình phân tích">{steps.map((step, index) => <li key={step} className={index < active ? "complete" : ""}><span>{index + 1}</span>{step}</li>)}</ol>;
}
