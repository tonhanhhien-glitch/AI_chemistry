import { Link } from "react-router-dom";

export default function HomePage() {
  return (
    <main className="page page--centered">
      <section className="hero">
        <p className="eyebrow">VSEPR-AI</p>
        <h1>Check a chemical formula</h1>
        <p className="lede">
          This stable baseline analyzes formulas using deterministic rules and
          displays atom counts and charge.
        </p>
        <Link className="button button--link" to="/analysis">
          Start analysis
        </Link>
      </section>
    </main>
  );
}
