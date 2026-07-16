import type { ClubType } from "../api/types";

// Visualization-only proportions -- not used in any calculation, same
// treatment as club_diagram.py's HEAD_VISUAL_LENGTH/GRIP_LENGTH constants.
// This is a stylized, parametric representation, not manufacturable geometry:
// there is no real clubhead mesh data anywhere in this project.
export const GRIP_LENGTH_IN = 10;
export const SHAFT_TIP_RADIUS_IN = 0.23;
export const SHAFT_BUTT_RADIUS_IN = 0.3;
export const GRIP_RADIUS_IN = 0.45;

export interface HeadShape {
  kind: "rounded" | "blade";
  width: number;  // along the club-length axis
  height: number; // crown to sole
  depth: number;  // face to back
}

const BASE_HEAD_SHAPES: Record<ClubType, HeadShape> = {
  driver: { kind: "rounded", width: 4.6, height: 2.8, depth: 3.2 },
  wood: { kind: "rounded", width: 3.2, height: 2.2, depth: 2.4 },
  hybrid: { kind: "rounded", width: 2.4, height: 1.9, depth: 1.9 },
  iron: { kind: "blade", width: 1.6, height: 2.2, depth: 0.6 },
  wedge: { kind: "blade", width: 1.7, height: 2.1, depth: 0.7 },
};

const REFERENCE_HEAD_MASS = 200; // grams -- roughly a driver head, used as the scaling baseline

// Head volume scales roughly with mass (cube-root of a mass ratio keeps a
// heavier head looking proportionally bigger without exaggerating it), then
// clamped so extreme inputs don't produce an absurd or invisible model.
export function getHeadShape(clubType: ClubType, headMass: number): HeadShape {
  const base = BASE_HEAD_SHAPES[clubType];
  const rawScale = Math.cbrt(Math.max(headMass, 20) / REFERENCE_HEAD_MASS);
  const scale = Math.min(1.35, Math.max(0.75, rawScale));
  return {
    kind: base.kind,
    width: base.width * scale,
    height: base.height * scale,
    depth: base.depth * scale,
  };
}
