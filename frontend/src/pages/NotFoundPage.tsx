import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <main className="page page--centered">
      <section className="card not-found">
        <p className="eyebrow">404</p>
        <h1>Page not found</h1>
        <p>The requested path does not exist.</p>
        <Link to="/">Return to home</Link>
      </section>
    </main>
  );
}
