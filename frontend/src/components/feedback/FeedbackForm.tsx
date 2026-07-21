import { useState } from "react";
import { useFeedback } from "../../hooks/useFeedback";
import RatingWidget from "./RatingWidget";

export default function FeedbackForm({ moleculeId }: { moleculeId: string }) {
  const [rating, setRating] = useState(5); const [comment, setComment] = useState(""); const [category, setCategory] = useState<"clarity" | "usefulness" | "chemistry_error" | "other">("usefulness"); const { submit, status, isLoading } = useFeedback();
  return <form className="feedback-form" onSubmit={(event) => { event.preventDefault(); void submit({ session_id: localStorage.getItem("vsepr-session") || undefined, molecule_id: moleculeId, rating, category, comment: comment || undefined }); }}><RatingWidget value={rating} onChange={setRating} /><label>Loại phản hồi<select value={category} onChange={(event) => setCategory(event.target.value as typeof category)}><option value="usefulness">Mức hữu ích</option><option value="clarity">Độ rõ ràng</option><option value="chemistry_error">Nghi ngờ lỗi hoá học</option><option value="other">Khác</option></select></label><label>Ghi chú (không nhập tên hoặc mã sinh viên)<textarea value={comment} onChange={(event) => setComment(event.target.value)} maxLength={1000} /></label><button disabled={isLoading}>{isLoading ? "Đang gửi…" : "Gửi phản hồi ẩn danh"}</button>{status && <p role="status">{status}</p>}</form>;
}
