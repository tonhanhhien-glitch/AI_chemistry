import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Html, Line } from "@react-three/drei";
import { useMemo, useRef } from "react";
import * as THREE from "three";

type Coordinate = [number, number, number];

type Atom = {
  element?: string;
  symbol?: string;
  is_central?: boolean;
};

type Props = {
  coordinates: Coordinate[];
  atoms: Atom[] | Record<string, Atom>;

  bondAngle?: number;
  electronGeometry?: string;
  molecularGeometry?: string;

  electronDomains?: number;
  bondingPairs?: number;
  lonePairs?: number;

  animate?: boolean;
  showDomains?: boolean;
};

const COLORS: Record<string, string> = {
  H: "#FFFFFF",
  C: "#555555",
  O: "#D60018",
  N: "#2E6CF6",
  F: "#0B8F2F",
  Cl: "#2BA84A",
  Br: "#8B4513",
  I: "#6A3D9A",
  P: "#F57C00",
  S: "#F4C542",
  B: "#147A5A",
};

const RADII: Record<string, number> = {
  H: 0.22,
  C: 0.28,
  O: 0.28,
  N: 0.28,
  F: 0.30,
  Cl: 0.35,
  Br: 0.38,
  I: 0.42,
  P: 0.34,
  S: 0.34,
  B: 0.28,
};

function idealAngle(domains: number) {
  switch (domains) {
    case 2: return 180;
    case 3: return 120;
    case 4: return 109.5;
    case 5: return 120;
    case 6: return 90;
    default: return 109.5;
  }
}

const VSEPR_POSITIONS: Record<string, Coordinate[]> = {
  AX2: [[-1,0,0],[1,0,0]],
  AX3: [[0,0.9,0],[-0.78,-0.45,0],[0.78,-0.45,0]],
  AX2E: [[-0.75,-0.3,0],[0.75,-0.3,0]],

  AX4: [
    [0,0.95,0],
    [-0.82,-0.25,0.58],
    [0.82,-0.25,0.58],
    [0,-0.45,-0.82],
  ],

  AX3E: [
    [0,0.85,0],
    [-0.75,-0.2,0.5],
    [0.75,-0.2,0.5],
  ],

  AX2E2: [
    [-0.72,-0.18,0],
    [0.72,-0.18,0],
  ],

  AX5: [
    [0,1,0],
    [0,-1,0],
    [-0.82,0,0],
    [0.82,0,0],
    [0,0,0.82],
  ],

  AX4E: [
    [0,1,0],
    [-0.8,0,0],
    [0.8,0,0],
    [0,0,0.8],
  ],

  AX3E2: [
    [0,1,0],
    [-0.8,0,0],
    [0.8,0,0],
  ],

  AX2E3: [
    [-1,0,0],
    [1,0,0],
  ],

  AX6: [
    [1,0,0],[-1,0,0],
    [0,1,0],[0,-1,0],
    [0,0,1],[0,0,-1],
  ],

  AX5E: [
    [1,0,0],[-1,0,0],
    [0,1,0],[0,-1,0],
    [0,0,1],
  ],

  AX4E2: [
    [1,0,0],[-1,0,0],
    [0,1,0],[0,-1,0],
  ],
};

function AnimatedAtom({
  from,
  to,
  element,
  animate,
}:{
  from:Coordinate;
  to:Coordinate;
  element:string;
  animate:boolean;
}){

  const ref=useRef<THREE.Mesh>(null);

  useFrame((_,delta)=>{

    if(!ref.current) return;

    const target=animate?to:from;

    ref.current.position.lerp(
      new THREE.Vector3(...target),
      delta*2
    );
  });

  return(
    <mesh ref={ref} position={from}>
      <sphereGeometry args={[RADII[element]??0.28,32,32]}/>
      <meshStandardMaterial color={COLORS[element]??"#999"}/>
    </mesh>
  );
}

function Bond({
  start,
  end,
}:{
  start:Coordinate;
  end:Coordinate;
}){

  const startV=new THREE.Vector3(...start);
  const endV=new THREE.Vector3(...end);

  const dir=new THREE.Vector3().subVectors(endV,startV);
  const length=dir.length();

  const mid=new THREE.Vector3()
    .addVectors(startV,endV)
    .multiplyScalar(.5);

  const quat=new THREE.Quaternion().setFromUnitVectors(
    new THREE.Vector3(0,1,0),
    dir.clone().normalize()
  );

  return(
    <mesh position={mid} quaternion={quat}>
      <cylinderGeometry args={[0.06,0.06,length,20]}/>
      <meshStandardMaterial color="#444"/>
    </mesh>
  );
}

function LonePair({
  position,
}:{
  position:Coordinate;
}){

  return(
    <mesh position={position}>
      <sphereGeometry args={[0.14,20,20]}/>
      <meshStandardMaterial
        color="#B14EFF"
        transparent
        opacity={.45}
      />
    </mesh>
  );
}

function DomainGuide({
  center,
  end,
}:{
  center:Coordinate;
  end:Coordinate;
}){

  return(
    <Line
      points={[center,end]}
      color="#B14EFF"
      dashed
      dashSize={0.08}
      gapSize={0.05}
      lineWidth={1}
    />
  );
}

function AngleArc({
  center,
  terminals,
  angle,
  animate,
  electronDomains,
}:{
  center:Coordinate;
  terminals:Coordinate[];
  angle?:number;
  animate?:boolean;
  electronDomains?:number;
}){

  const displayAngle=useRef(
    idealAngle(electronDomains??4)
  );

  useFrame((_,delta)=>{

    if(angle===undefined) return;

    const start=idealAngle(electronDomains??4);

    if(animate){
      displayAngle.current+=
        (angle-displayAngle.current)*delta*2;
    }else{
      displayAngle.current=start;
    }

  });

  if(terminals.length<2||angle===undefined) return null;

  const p1=new THREE.Vector3(...terminals[0]);
  const p2=new THREE.Vector3(...terminals[1]);
  const c=new THREE.Vector3(...center);

  const mid=new THREE.Vector3()
    .addVectors(p1,p2)
    .multiplyScalar(.5);

  mid.lerp(c,.25);

  return(
    <Html position={mid.toArray() as Coordinate} center>
      <div
        style={{
          background:"rgba(255,255,255,.95)",
          border:"2px solid #147A5A",
          borderRadius:999,
          padding:"4px 10px",
          fontWeight:700,
          color:"#147A5A",
          whiteSpace:"nowrap",
        }}
      >
        {displayAngle.current.toFixed(1)}°
      </div>
    </Html>
  );
}

export default function MoleculeViewer({
  coordinates,
  atoms,
  bondAngle,
  electronDomains,
  bondingPairs=0,
  lonePairs=0,
  animate=false,
  showDomains=false,
}:Props){

  const atomList=Array.isArray(atoms)
    ?atoms
    :Object.values(atoms);

  const centerIndex=
    atomList.findIndex(a=>a.is_central)>=0
      ?atomList.findIndex(a=>a.is_central)
      :0;

  const center=coordinates[centerIndex];

  const terminals=coordinates.filter((_,i)=>i!==centerIndex);

  const vseprKey=`AX${bondingPairs}E${lonePairs}`.replace("E0","");

  const targetPositions=VSEPR_POSITIONS[vseprKey]??terminals;

  const domainPositions=useMemo(()=>{

    const make=(x:number,y:number,z:number):Coordinate=>[
      center[0]+x,
      center[1]+y,
      center[2]+z,
    ];

    switch(electronDomains){

      case 2:
        return[
          make(-0.8,0,0),
          make(0.8,0,0),
        ];

      case 3:
        return[
          make(0,0.7,0),
          make(-0.6,-0.35,0),
          make(0.6,-0.35,0),
        ];

      case 4:
        return[
          make(0,0.72,0),
          make(-0.62,-0.12,0.42),
          make(0.62,-0.12,0.42),
          make(0,-0.18,-0.62),
        ];

      case 5:
        return[
          make(0,0.9,0),
          make(0,-0.9,0),
          make(-0.7,0,0),
          make(0.7,0,0),
          make(0,0,0.7),
        ];

      case 6:
        return[
          make(0.8,0,0),
          make(-0.8,0,0),
          make(0,0.8,0),
          make(0,-0.8,0),
          make(0,0,0.8),
          make(0,0,-0.8),
        ];

      default:
        return[];

    }

  },[center,electronDomains]);

  const electronPositions=useMemo(()=>{

    if(!showDomains) return[];

    return domainPositions
      .slice(bondingPairs)
      .slice(0,lonePairs);

  },[
    domainPositions,
    bondingPairs,
    lonePairs,
    showDomains,
  ]);

  return(
    <Canvas camera={{position:[0,0,4],fov:45}}>

      <ambientLight intensity={1.3}/>
      <directionalLight position={[3,3,3]} intensity={2}/>

      <OrbitControls enableDamping/>

      {atomList.map((atom,i)=>{

        const start=coordinates[i];

        const end =
          i === centerIndex
            ? start
            : (targetPositions[i - 1] ?? start);

        return(
          <AnimatedAtom
            key={i}
            from={start}
            to={end}
            animate={animate}
            element={atom.element??atom.symbol??"C"}
          />
        );

      })}

      {terminals.map((coord,i)=>(
        <Bond
          key={i}
          start={center}
          end={coord}
        />
      ))}

      {showDomains&&
        domainPositions.map((p,i)=>(
          <DomainGuide
            key={i}
            center={center}
            end={p}
          />
        ))}

      {electronPositions.map((p,i)=>(
        <LonePair
          key={i}
          position={p}
        />
      ))}

      <AngleArc
        center={center}
        terminals={terminals}
        angle={bondAngle}
        animate={animate}
        electronDomains={electronDomains}
      />

    </Canvas>
  );

}