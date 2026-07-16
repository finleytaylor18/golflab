import { useMemo } from "react";
import { RoundedBox } from "@react-three/drei";
import type { ClubSpecification } from "../api/types";
import { getHeadShape, GRIP_LENGTH_IN, SHAFT_TIP_RADIUS_IN, SHAFT_BUTT_RADIUS_IN, GRIP_RADIUS_IN } from "./clubGeometry";

interface Props {
  club: ClubSpecification;
}

export function ClubMesh({ club }: Props) {
  const headShape = useMemo(
    () => getHeadShape(club.club_type, club.head_mass),
    [club.club_type, club.head_mass],
  );

  const shaftStart = GRIP_LENGTH_IN;
  const headX = club.club_length - headShape.width / 2;
  const shaftEnd = Math.max(headX - headShape.width / 2, shaftStart + 1);
  const shaftLength = shaftEnd - shaftStart;
  const shaftMid = shaftStart + shaftLength / 2;

  return (
    <group>
      <mesh position={[GRIP_LENGTH_IN / 2, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[GRIP_RADIUS_IN, GRIP_RADIUS_IN * 0.85, GRIP_LENGTH_IN, 24]} />
        <meshStandardMaterial color="#2a2f36" roughness={0.85} />
      </mesh>

      <mesh position={[shaftMid, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
        <cylinderGeometry args={[SHAFT_TIP_RADIUS_IN, SHAFT_BUTT_RADIUS_IN, shaftLength, 20]} />
        <meshStandardMaterial color="#a8afba" metalness={0.7} roughness={0.25} />
      </mesh>

      {headShape.family === "rounded" ? (
        <RoundedBox
          position={[headX, 0, 0]}
          args={[headShape.width, headShape.height, headShape.depth]}
          radius={Math.min(headShape.height, headShape.depth) * 0.22}
          smoothness={4}
        >
          <meshStandardMaterial color="#1d5fbf" metalness={0.45} roughness={0.3} />
        </RoundedBox>
      ) : (
        <mesh position={[headX, 0, 0]} rotation={[0, 0, (headShape.tiltDeg * Math.PI) / 180]}>
          <boxGeometry args={[headShape.width, headShape.height, headShape.depth]} />
          <meshStandardMaterial color="#1d5fbf" metalness={0.5} roughness={0.3} />
        </mesh>
      )}
    </group>
  );
}
