import { Line } from "@react-three/drei";
import type { Coordinate } from "./types";

type Props = {
  center: Coordinate;
  end: Coordinate;
};

export default function DomainGuide({ center, end }: Props) {
  return (
    <Line
      points={[center, end]}
      color="#B14EFF"
      dashed
      dashSize={0.08}
      gapSize={0.05}
      lineWidth={1}
    />
  );
}