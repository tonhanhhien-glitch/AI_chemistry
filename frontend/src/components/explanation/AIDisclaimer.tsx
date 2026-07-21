export default function AIDisclaimer({ source }: { source: "claude" | "deterministic_fallback" }) {
  return <p className="ai-disclaimer"><strong>{source === "claude" ? "Claude đã diễn giải" : "Bản giải thích xác định"}</strong> · Các kết luận Lewis, AXnEm, hình học và góc đến từ bộ quy tắc và không thể bị AI thay đổi.</p>;
}
