import { Html } from "@react-three/drei";
import { useFrame } from "@react-three/fiber";
import { useRef } from "react";
import * as THREE from "three";
import type { Coordinate } from "./types";

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

type Props = {
  center: Coordinate;
  terminals: Coordinate[];
  angle?: number;
  animate?: boolean;
  electronDomains?: number;
};

export default function AngleArc({
  center,
  terminals,
  angle,
  animate,
  electronDomains = 4,
}: Props) {

  const current = useRef(idealAngle(electronDomains));

  useFrame((_, delta) => {

    if (!angle) return;

    const target = animate ? angle : idealAngle(electronDomains);

    current.current += (target - current.current) * delta * 2;
  });

  if (terminals.length < 2 || !angle) return null;

  const p1 = new THREE.Vector3(...terminals[0]);
  const p2 = new THREE.Vector3(...terminals[1]);
  const c = new THREE.Vector3(...center);

  const mid = new THREE.Vector3()
    .addVectors(p1, p2)
    .multiplyScalar(0.5);

  mid.lerp(c, 0.25);

  return (
    <Html position={mid.toArray() as Coordinate} center>
      <div
        style={{
          background: "rgba(255,255,255,.95)",
          border: "2px solid #147A5A",
          borderRadius: 999,
          padding: "4px 10px",
          color: "#147A5A",
          fontWeight: 700,
          whiteSpace: "nowrap",
        }}
      >
        {current.current.toFixed(1)}°
      </div>
    </Html>
  );
}