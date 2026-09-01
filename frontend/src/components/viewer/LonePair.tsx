import type { Coordinate } from "./types";

export default function LonePair({
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
        opacity={0.45}
      />
    </mesh>
  );
}