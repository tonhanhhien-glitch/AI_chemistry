export default function AXENotationBadge({ notation }: { notation: string }) {
  return <span className="ax-badge" aria-label={`Ký hiệu VSEPR ${notation}`}>{notation}</span>;
}
