import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import AnimatedAtom from "../viewer/AnimatedAtom";
import Bond from "../viewer/Bond";
import AngleArc from "../viewer/AngleArc";
import DomainGuide from "../viewer/DomainGuide";
import LonePair from "../viewer/LonePair";
import { VSEPR_POSITIONS } from "../viewer/VSEPR_POSITIONS";

type Coordinate = [number, number, number];

type Atom = {
  element?: string;
  symbol?: string;
  is_central?: boolean;
};

type BackendCoordinate = {
  atom_index: number;
  role: string;
  coordinate: Coordinate;
};

type Props = {
  coordinates: BackendCoordinate[];
  atoms: Atom[] | Record<string, Atom>;
  bondAngle?: number;
  electronDomains?: number;
  bondingPairs?: number;
  lonePairs?: number;
  animate?: boolean;
  showDomains?: boolean;
};

export default function Viewer3D({
  coordinates,
  atoms,
  bondAngle,
  electronDomains,
  bondingPairs = 0,
  lonePairs = 0,
  animate = false,
  showDomains = true,
}: Props) {

  const atomList = Array.isArray(atoms)
    ? atoms
    : Object.values(atoms);

  const coords = coordinates.map((c) => c.coordinate);

  const centerIndex =
    atomList.findIndex((a) => a.is_central) >= 0
      ? atomList.findIndex((a) => a.is_central)
      : 0;

  const center = coords[centerIndex];

  const terminals = coords.filter((_, i) => i !== centerIndex);

  const key =
    `AX${bondingPairs}E${lonePairs}`.replace("E0", "");

  const targetPositions = VSEPR_POSITIONS[key] ?? coords;

  const domainPositions =
    targetPositions.slice(0, electronDomains ?? 0);

  const lonePairPositions =
    domainPositions.slice(bondingPairs);

  return (
    <Canvas camera={{ position: [0,0,4], fov:45 }}>
      <ambientLight intensity={1.3}/>
      <directionalLight position={[3,3,3]} intensity={2}/>

      <OrbitControls enableDamping/>

      {coords.map((coord,i)=>(
        <AnimatedAtom
          key={i}
          from={coord}
          to={targetPositions[i] ?? coord}
          element={
            atomList[i]?.element ??
            atomList[i]?.symbol ??
            "C"
          }
          animate={animate}
        />
      ))}

      {terminals.map((coord,i)=>(
        <Bond
          key={i}
          start={center}
          end={coord}
        />
      ))}

      {showDomains &&
        domainPositions.map((p,i)=>(
          <DomainGuide
            key={i}
            center={center}
            end={p}
          />
        ))}

      {showDomains &&
        lonePairPositions.map((p,i)=>(
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