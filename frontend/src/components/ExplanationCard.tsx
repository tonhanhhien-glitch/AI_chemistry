type Props = {
  result: any;
};

function buildExplanation(data: any) {
  const geometry = data.vsepr?.molecular_geometry ?? "";
  const electronGeometry = data.vsepr?.electron_geometry ?? "";
  const angle = data.vsepr?.characteristic_bond_angle ?? "";
  const central = data.central_atom ?? "";

  switch (geometry.toLowerCase()) {
    case "bent":
      return {
        title: "AX₂E₂ – Bent",
        text: `Nguyên tử trung tâm là ${central}. Có hai cặp electron liên kết và hai cặp electron tự do. Theo VSEPR, các cặp electron tự do đẩy mạnh hơn cặp electron liên kết nên góc liên kết giảm xuống khoảng ${angle}°.`
      };

    case "linear":
      return {
        title: "AX₂ – Linear",
        text: `Hai vùng mật độ electron nằm đối diện nhau nên phân tử tạo thành đường thẳng với góc 180°.`
      };

    case "tetrahedral":
      return {
        title: "AX₄ – Tetrahedral",
        text: `Có bốn vùng mật độ electron xung quanh ${central}, phân bố đều trong không gian nên góc gần 109.5°.`
      };

    case "trigonal pyramidal":
      return {
        title: "AX₃E – Trigonal Pyramidal",
        text: `Một cặp electron tự do làm tăng lực đẩy nên hình học phân tử trở thành chóp tam giác và góc nhỏ hơn 109.5°.`
      };

    case "trigonal planar":
      return {
        title: "AX₃ – Trigonal Planar",
        text: `Ba vùng mật độ electron phân bố đều trên cùng một mặt phẳng tạo góc khoảng 120°.`
      };

    case "trigonal bipyramidal":
      return {
        title: "AX₅ – Trigonal Bipyramidal",
        text: `Năm vùng mật độ electron phân bố theo hai vị trí trục và ba vị trí xích đạo.`
      };

    case "octahedral":
      return {
        title: "AX₆ – Octahedral",
        text: `Sáu vùng mật độ electron phân bố đối xứng quanh nguyên tử trung tâm.`
      };

    default:
      return {
        title: geometry || "VSEPR",
        text: `Phân tử được phân tích theo quy tắc VSEPR. Electron geometry là ${electronGeometry}, molecular geometry là ${geometry}.`
      };
  }
}

export default function ExplanationCard({ result }: Props) {
  const data = result.data;
  const explanation = buildExplanation(data);

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
          ✨ AI Teacher Mode
        </h3>
      </div>

      <div
        style={{
          padding: 24,
        }}
      >
        <div
          style={{
            display: "inline-block",
            background: "#147A5A",
            color: "white",
            padding: "6px 12px",
            borderRadius: 999,
            fontSize: 13,
            fontWeight: 600,
            marginBottom: 18,
          }}
        >
          {explanation.title}
        </div>

        <p
          style={{
            lineHeight: 1.9,
            color: "#344054",
            marginBottom: 18,
          }}
        >
          {explanation.text}
        </p>

        <div
          style={{
            background: "#EEF8F3",
            borderLeft: "4px solid #147A5A",
            padding: 16,
            borderRadius: 10,
          }}
        >
          <strong>Ghi nhớ nhanh</strong>

          <p
            style={{
              marginTop: 8,
              lineHeight: 1.7,
            }}
          >
            Electron tự do luôn tạo lực đẩy mạnh hơn electron liên kết, vì vậy chúng thường làm giảm góc liên kết của phân tử.
          </p>
        </div>
      </div>
    </div>
  );
}