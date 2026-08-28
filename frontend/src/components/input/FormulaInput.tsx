type Props = {
  formula: string;
  loading: boolean;
  onChange: (value: string) => void;
  onAnalyze: () => void;
};

const examples = ["H2O","CO2","NH3","CH4","BF3","PCl5","SF6"];

export default function FormulaInput({
  formula,
  loading,
  onChange,
  onAnalyze,
}: Props) {
  return (
    <div style={{ marginBottom: 30 }}>
      <div style={{ display: "flex", gap: 12 }}>
        <input
          value={formula}
          onChange={(e)=>onChange(e.target.value)}
          style={{
            flex:1,
            padding:14,
            borderRadius:14,
            border:"1px solid #CCC",
            fontSize:16
          }}
        />

        <button
          onClick={onAnalyze}
          disabled={loading}
          style={{
            padding:"14px 22px",
            borderRadius:14,
            border:"none",
            background:"#147A5A",
            color:"white",
            fontWeight:700,
            cursor:"pointer"
          }}
        >
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </div>

      <div
        style={{
          display:"flex",
          gap:10,
          flexWrap:"wrap",
          marginTop:20
        }}
      >
        {examples.map((f)=>(
          <button
            key={f}
            onClick={()=>onChange(f)}
            style={{
              padding:"8px 14px",
              borderRadius:999,
              border:"1px solid #D8E3DD",
              background: formula===f ? "#147A5A" : "white",
              color: formula===f ? "white" : "#1F3A32",
              cursor:"pointer"
            }}
          >
            {f}
          </button>
        ))}
      </div>
    </div>
  );
}