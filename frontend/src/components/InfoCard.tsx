type Props = {
  result: any;
};

export default function InfoCard({ result }: Props) {
  const data = result.data;

  const rows = [
    {
      label: "Formula",
      value: data.formula,
      icon: "🧪",
    },
    {
      label: "Central Atom",
      value: data.central_atom,
      icon: "⚛️",
    },
    {
      label: "Molecular Geometry",
      value: data.vsepr?.molecular_geometry,
      icon: "📐",
    },
    {
      label: "Electron Geometry",
      value: data.vsepr?.electron_geometry,
      icon: "🔷",
    },
    {
      label: "Bond Angle",
      value: `${data.vsepr?.characteristic_bond_angle}°`,
      icon: "📏",
    },
    {
      label: "Formal Charge",
      value: data.lewis?.total_formal_charge,
      icon: "➕",
    },
    {
      label: "Resonance",
      value: data.resonance?.is_resonance ? "Có" : "Không",
      icon: "🔄",
    },
  ];

  return (
    <div
      style={{
        background: "white",
        borderRadius: 18,
        border: "1px solid #D8E3DD",
        boxShadow: "0 8px 20px rgba(0,0,0,.05)",
        overflow: "hidden",
      }}
    >
      {/* Header */}

      <div
        style={{
          background: "#147A5A",
          color: "white",
          padding: "18px 24px",
        }}
      >
        <h2 style={{ margin: 0 }}>{data.formula}</h2>

        <p
          style={{
            marginTop: 6,
            opacity: 0.9,
          }}
        >
          VSEPR Analysis
        </p>
      </div>

      {/* Content */}

      <div
        style={{
          padding: 24,
          display: "grid",
          gap: 14,
        }}
      >
        {rows.map((row) => (
          <div
            key={row.label}
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              paddingBottom: 10,
              borderBottom: "1px solid #EEF3EF",
            }}
          >
            <div
              style={{
                display: "flex",
                gap: 10,
                alignItems: "center",
              }}
            >
              <span>{row.icon}</span>

              <span
                style={{
                  color: "#5F6E67",
                }}
              >
                {row.label}
              </span>
            </div>

            <strong
              style={{
                color: "#0F2F28",
              }}
            >
              {row.value}
            </strong>
          </div>
        ))}
      </div>
    </div>
  );
}