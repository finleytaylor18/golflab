import type { ClubSpecification } from "../api/types";
import { HEAD_PATHS, HOSEL_POINT, GRIP_TOP, GRIP_BOTTOM, GROUND_Y, VIEW_WIDTH, VIEW_HEIGHT } from "./clubSilhouettes";

interface Props {
  club: ClubSpecification;
}

const REFERENCE_CLUB_LENGTH = 45; // inches -- roughly a driver, baseline for the overall scale
const REFERENCE_HEAD_MASS = 200; // grams -- baseline for the head-only scale

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

export function ClubIllustration({ club }: Props) {
  const overallScale = clamp(club.club_length / REFERENCE_CLUB_LENGTH, 0.85, 1.1);
  const headScale = clamp(Math.cbrt(club.head_mass / REFERENCE_HEAD_MASS), 0.85, 1.2);

  return (
    <svg viewBox={`0 0 ${VIEW_WIDTH} ${VIEW_HEIGHT}`} className="club-illustration" role="img" aria-label={`${club.club_type} silhouette`}>
      <g
        transform={`translate(${VIEW_WIDTH / 2},${VIEW_HEIGHT / 2}) scale(${overallScale}) translate(${-VIEW_WIDTH / 2},${-VIEW_HEIGHT / 2})`}
      >
        <line x1={16} y1={GROUND_Y} x2={VIEW_WIDTH - 16} y2={GROUND_Y} className="ground-line" />

        <line x1={GRIP_BOTTOM.x} y1={GRIP_BOTTOM.y} x2={HOSEL_POINT.x} y2={HOSEL_POINT.y} className="club-shaft" />
        <line x1={GRIP_TOP.x} y1={GRIP_TOP.y} x2={GRIP_BOTTOM.x} y2={GRIP_BOTTOM.y} className="club-grip" />

        <g
          transform={`translate(${HOSEL_POINT.x},${HOSEL_POINT.y}) scale(${headScale}) translate(${-HOSEL_POINT.x},${-HOSEL_POINT.y})`}
        >
          <path d={HEAD_PATHS[club.club_type]} className="club-head" />
        </g>
      </g>
    </svg>
  );
}
