import * as THREE from "three";
import type { Coordinate } from "./types";

export default function Bond({
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