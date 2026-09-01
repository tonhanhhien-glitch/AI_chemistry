import { useFrame } from "@react-three/fiber";
import { useRef } from "react";
import * as THREE from "three";
import type { Coordinate } from "./types";

const COLORS: Record<string,string> = {
  H:"#FFFFFF",
  C:"#555555",
  O:"#D60018",
  N:"#2E6CF6",
  F:"#0B8F2F",
  Cl:"#2BA84A",
  Br:"#8B4513",
  I:"#6A3D9A",
  P:"#F57C00",
  S:"#F4C542",
  B:"#147A5A",
};

const RADII: Record<string,number> = {
  H:0.22,C:0.28,O:0.28,N:0.28,
  F:0.30,Cl:0.35,Br:0.38,I:0.42,
  P:0.34,S:0.34,B:0.28,
};

export default function AnimatedAtom({
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