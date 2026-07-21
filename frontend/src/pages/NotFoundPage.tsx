import { Link } from "react-router-dom";
import PageContainer from "../components/layout/PageContainer";

export default function NotFoundPage() {
  return <PageContainer><section className="not-found"><p className="eyebrow">Lỗi 404</p><h1>Không tìm thấy trang</h1><p>Đường dẫn này không tồn tại hoặc đã thay đổi.</p><Link className="button button--link" to="/">Về trang chủ</Link></section></PageContainer>;
}
