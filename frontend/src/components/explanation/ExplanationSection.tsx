import { formatChemText } from "../../utils/chemFormula";

export default function ExplanationSection({ title, children }: { title: string; children: string }) {
  return <section className="explanation-section"><h3>{title}</h3><p>{formatChemText(children)}</p></section>;
}
