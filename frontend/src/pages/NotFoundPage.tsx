import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <main className="page page--centered">
      <section className="card not-found">
        <p className="eyebrow">404</p>
        <h1>Không tìm thấy trang</h1>
        <p>Đường dẫn bạn yêu cầu không tồn tại.</p>
        <Link to="/">Quay về trang chủ</Link>
      </section>
    </main>
  );
}
