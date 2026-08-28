type Props = {
  showAngle: boolean;
  showLonePairs: boolean;
  showDomains: boolean;
  animate: boolean;

  setShowAngle: (v:boolean)=>void;
  setShowLonePairs: (v:boolean)=>void;
  setShowDomains: (v:boolean)=>void;
  setAnimate: (v:boolean)=>void;
};

function Toggle({
  label,
  checked,
  onChange
}:{
  label:string;
  checked:boolean;
  onChange:(v:boolean)=>void;
}){

  return(
    <button
      onClick={()=>onChange(!checked)}
      style={{
        display:"flex",
        justifyContent:"space-between",
        alignItems:"center",
        width:"100%",
        padding:"12px 14px",
        borderRadius:14,
        border:"1px solid #E5ECE8",
        background:checked?"#147A5A":"white",
        color:checked?"white":"#0F2F28",
        cursor:"pointer"
      }}
    >
      <span>{label}</span>

      <span>{checked?"ON":"OFF"}</span>
    </button>
  );
}

export default function ViewerControls(props:Props){

  return(

    <div
      style={{
        background:"rgba(255,255,255,.82)",
        backdropFilter:"blur(18px)",
        border:"1px solid #E5ECE8",
        borderRadius:18,
        padding:18,
        display:"grid",
        gap:12
      }}
    >
      <h3
        style={{
          margin:0
        }}
      >
        Visualization
      </h3>

      <Toggle
        label="🟢 Show Bond Angle"
        checked={props.showAngle}
        onChange={props.setShowAngle}
      />

      <Toggle
        label="🔵 Show Lone Pairs"
        checked={props.showLonePairs}
        onChange={props.setShowLonePairs}
      />

      <Toggle
        label="🟣 Show Electron Domains"
        checked={props.showDomains}
        onChange={props.setShowDomains}
      />

      <button
        onClick={() => props.setAnimate(true)}
        style={{
            padding: "14px",
            borderRadius: 14,
            border: "none",
            background: "#147A5A",
            color: "white",
            fontWeight: 700,
            cursor: "pointer",
        }}
        >
        ✨ Play VSEPR Animation
        </button>
    </div>

  );
}