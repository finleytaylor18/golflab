import { Canvas } from "@react-three/fiber";
import { OrbitControls, Grid } from "@react-three/drei";
import { ClubMesh } from "./ClubMesh";
import type { ClubSpecification } from "../api/types";

interface Props {
  club: ClubSpecification;
}

export function ClubScene({ club }: Props) {
  const center = club.club_length / 2;

  // Camera distance/height scale with club_length rather than being fixed,
  // so a short wedge and a long driver both frame well. A flat-ish elevation
  // angle (~10 deg) reads as a product-shot profile view instead of a
  // steep top-down angle, which put the club near the bottom edge of frame
  // against a dominant grid horizon during earlier tuning.
  const distance = club.club_length * 1.15 + 18;
  const height = club.club_length * 0.18 + 4;

  return (
    <Canvas camera={{ position: [center, height, distance], fov: 30 }} dpr={[1, 2]}>
      <ambientLight intensity={0.7} />
      <directionalLight position={[30, 40, 20]} intensity={1.3} />
      <directionalLight position={[-20, 10, -25]} intensity={0.35} />
      <Grid
        position={[center, -3, 0]}
        args={[60, 60]}
        cellColor="#3a3f47"
        sectionColor="#4a5057"
        fadeDistance={50}
        fadeStrength={1}
      />
      <ClubMesh club={club} />
      <OrbitControls
        target={[center, 0, 0]}
        minDistance={10}
        maxDistance={150}
        enableDamping
        dampingFactor={0.1}
      />
    </Canvas>
  );
}
