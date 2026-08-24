type Props = {
  formula: string;
  loading: boolean;
  onChange: (value: string) => void;
  onAnalyze: (formula?: string) => void;
};

const examples = ["H2O", "CO2", "NH3", "CH4", "BF3", "PCl5", "SF6"];

export default function FormulaInput({
  formula,
  loading,
  onChange,
  onAnalyze,
}: Props) {
  return (
    <>
      {/* Thanh nhập công thức */}
      <div
        style={{
          display: "flex",
          gap: 12,
          marginBottom: 18,
        }}
      >
        <input
          value={formula}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Ví dụ: H2O, CO2, NH3..."
          onKeyDown={(e) => {
            if (e.key === "Enter") onAnalyze();
          }}
          style={{
            flex: 1,
            padding: 14,
            borderRadius: 14,
            border: "1px solid #CCC",
            fontSize: 16,
          }}
        />

        <button
          onClick={() => onAnalyze()}
          disabled={loading}
          style={{
            padding: "14px 22px",
            borderRadius: 14,
            border: "none",
            background: "#147A5A",
            color: "white",
            fontWeight: 700,
            cursor: "pointer",
          }}
        >
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </div>

      {/* Quick Examples */}
      <div
        style={{
          display: "flex",
          gap: 10,
          flexWrap: "wrap",
          marginBottom: 28,
        }}
      >
        {examples.map((item) => (
          <button
            key={item}
            onClick={() => onAnalyze(item)}
            disabled={loading}
            style={{
              padding: "8px 14px",
              borderRadius: 999,
              border: "1px solid #D8E3DD",
              background: formula === item ? "#147A5A" : "white",
              color: formula === item ? "white" : "#0F2F28",
              cursor: "pointer",
              fontWeight: 500,
            }}
          >
            {item}
          </button>
        ))}
      </div>
    </>
  );
}