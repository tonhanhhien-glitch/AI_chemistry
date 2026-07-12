import { Link } from "react-router-dom";

export default function HomePage() {
  return (
    <main className="page page--centered">
      <section className="hero">
        <p className="eyebrow">VSEPR-AI</p>
        <h1>Kiểm tra công thức hóa học</h1>
        <p className="lede">
          Bản nền ổn định này phân tích công thức bằng quy tắc xác định và hiển
          thị số nguyên tử cùng điện tích.
        </p>
        <Link className="button button--link" to="/analysis">
          Bắt đầu phân tích
        </Link>
      </section>
    </main>
  );
}
