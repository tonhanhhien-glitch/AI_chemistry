import FeedbackForm from "./FeedbackForm";

export default function ErrorReportForm({ moleculeId }: { moleculeId: string }) {
  return <details><summary>Báo cáo nghi ngờ sai hoá học</summary><p>Chọn “Nghi ngờ lỗi hoá học” và mô tả chính xác nguyên tử, điện tích hoặc góc cần kiểm tra.</p><FeedbackForm moleculeId={moleculeId} /></details>;
}
