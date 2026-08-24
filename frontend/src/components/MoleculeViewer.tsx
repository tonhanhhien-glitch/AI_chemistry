import * as THREE from "three";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";

type Coordinate = {
  atom_index: number;
  role: string;
  coordinate: [number, number, number];
};

type Atom = {
  symbol: string;
};

type Props = {
  coordinates: Coordinate[];
  atoms: Record<string, Atom>;
};

const COLORS: Record<string, string> = {
  H: "#FFFFFF",
  C: "#424242",
  O: "#D32F2F",
  N: "#2962FF",
  F: "#43A047",
  Cl: "#2E7D32",
  S: "#FBC02D",
  P: "#EF6C00",
  Br: "#8D6E63",
  I: "#6A1B9A",
};

function AtomSphere({
  position,
  color,
}: {
  position: [number, number, number];
  color: string;
}) {
  return (
    <mesh position={position}>
      <sphereGeometry args={[0.18, 32, 32]} />
      <meshStandardMaterial color={color} />
    </mesh>
  );
}

function Bond({
  start,
  end,
}: {
  start: [number, number, number];
  end: [number, number, number];
}) {
  const startVec = new THREE.Vector3(...start);
  const endVec = new THREE.Vector3(...end);

  const direction = endVec.clone().sub(startVec);
  const midpoint = startVec.clone().add(endVec).multiplyScalar(0.5);

  const quaternion = new THREE.Quaternion();

  quaternion.setFromUnitVectors(
    new THREE.Vector3(0, 1, 0),
    direction.clone().normalize()
  );

  return (
    <mesh position={midpoint} quaternion={quaternion}>
      <cylinderGeometry args={[0.05, 0.05, direction.length(), 20]} />
      <meshStandardMaterial color="#808080" />
    </mesh>
  );
}

export default function MoleculeViewer({
  coordinates,
  atoms,
}: Props) {
  if (!coordinates || coordinates.length === 0) {
    return (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "grid",
          placeItems: "center",
          color: "#667085",
        }}
      >
        Chưa có mô hình 3D
      </div>
    );
  }

  const atomList = Object.values(atoms);

  const central = coordinates.find((c) => c.role === "central") ?? coordinates[0];

  const peripherals = coordinates.filter((c) => c.atom_index !== central.atom_index);

  return (
    <Canvas
      camera={{ position: [0, 0, 4], fov: 45 }}
      style={{ width: "100%", height: "100%" }}
    >
      <color attach="background" args={["#FFFFFF"]} />

      <ambientLight intensity={1.2} />

      <directionalLight position={[3, 3, 3]} intensity={2} />

      <directionalLight position={[-3, -3, -3]} intensity={0.8} />

      {coordinates.map((coord, index) => (
        <AtomSphere
          key={index}
          position={coord.coordinate}
          color={COLORS[atomList[index]?.symbol] ?? "#9E9E9E"}
        />
      ))}

      {peripherals.map((coord, index) => (
        <Bond
          key={index}
          start={central.coordinate}
          end={coord.coordinate}
        />
      ))}

      <OrbitControls
        makeDefault
        enableRotate
        enableZoom
        enablePan
        enableDamping
        dampingFactor={0.08}
        autoRotate
        autoRotateSpeed={0.8}
        minDistance={2}
        maxDistance={8}
      />
    </Canvas>
  );
}