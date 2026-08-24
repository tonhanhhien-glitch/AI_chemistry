type Props = {
  result: any;
};

function getLewisDisplay(data: any) {
  const formula = data.formula;

  // Nếu backend sau này trả Lewis text thì ưu tiên dùng
  if (data.lewis?.display) return data.lewis.display;
  if (data.lewis?.structure) return data.lewis.structure;

  // Fallback cho các phân tử demo
  switch (formula) {
    case "H2O":
      return "H—O—H";
    case "CO2":
      return "O=C=O";
    case "NH3":
      return "H\n |\nH—N—H";
    case "CH4":
      return "    H\n    |\nH—C—H\n    |\n    H";
    case "BF3":
      return "F\n \\\n  B—F\n /\nF";
    default:
      return formula;
  }
}

export default function LewisCard({ result }: Props) {
  const data = result.data;

  const atomObjects = data.lewis?.atom_objects ?? {};
  const atoms = Object.values(atomObjects) as any[];

  return (
    <div
      style={{
        background: "white",
        borderRadius: 18,
        border: "1px solid #D8E3DD",
        boxShadow: "0 8px 20px rgba(0,0,0,.05)",
        marginTop: 22,
        overflow: "hidden",
      }}
    >
      {/* Header */}

      <div
        style={{
          background: "#F5FAF7",
          padding: "18px 24px",
          borderBottom: "1px solid #E7EFEA",
        }}
      >
        <h3
          style={{
            margin: 0,
            color: "#0F2F28",
          }}
        >
          Lewis Structure
        </h3>
      </div>

      {/* Lewis */}

      <div
        style={{
          padding: 28,
          textAlign: "center",
        }}
      >
        <div
          style={{
            fontSize: 34,
            lineHeight: 1.4,
            whiteSpace: "pre-line",
            letterSpacing: 2,
            color: "#1B2A24",
            marginBottom: 26,
          }}
        >
          {getLewisDisplay(data)}
        </div>

        {/* Lone pairs */}

        {atoms.length > 0 && (
          <>
            <div
              style={{
                fontWeight: 600,
                color: "#0F2F28",
                marginBottom: 14,
              }}
            >
              Lone Pairs
            </div>

            <div
              style={{
                display: "flex",
                justifyContent: "center",
                gap: 22,
                flexWrap: "wrap",
              }}
            >
              {atoms.map((atom, index) => (
                <div
                  key={index}
                  style={{
                    background: "#F8FBF9",
                    border: "1px solid #E4ECE7",
                    borderRadius: 14,
                    padding: "12px 16px",
                    minWidth: 72,
                  }}
                >
                  <div
                    style={{
                      fontSize: 22,
                      fontWeight: 700,
                      color: "#0F2F28",
                    }}
                  >
                    {atom.symbol}
                  </div>

                  <div
                    style={{
                      marginTop: 6,
                      fontSize: 18,
                      letterSpacing: 2,
                    }}
                  >
                    {"••".repeat(atom.lone_pairs ?? 0)}
                  </div>

                  <div
                    style={{
                      marginTop: 6,
                      fontSize: 12,
                      color: "#667085",
                    }}
                  >
                    {atom.lone_pairs ?? 0} pair
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}