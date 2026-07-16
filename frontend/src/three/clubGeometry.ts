import type { ClubType } from "../api/types";

// Visualization-only proportions -- not used in any calculation, same
// treatment as club_diagram.py's HEAD_VISUAL_LENGTH/GRIP_LENGTH constants.
// This is a stylized, parametric representation, not manufacturable geometry:
// there is no real clubhead mesh data anywhere in this project. Each shape
// below is a fixed, hand-picked recipe per club type -- distinct enough to
// read as "driver" vs "iron" at a glance, not dynamically derived from any
// input beyond the overall mass-based scale applied in getHeadShape().
export const GRIP_LENGTH_IN = 10;
export const SHAFT_TIP_RADIUS_IN = 0.23;
export const SHAFT_BUTT_RADIUS_IN = 0.3;
export const GRIP_RADIUS_IN = 0.45;

export interface HeadShape {
  family: "rounded" | "blade";
  width: number;    // X, along the club-length axis (how far the head extends past the shaft tip)
  height: number;    // Y, crown to sole
  depth: number;     // Z, toe to heel
  tiltDeg: number;   // static rotation around the toe-heel axis, for a fixed "open face" look (wedge only)
}

// (family, width, height, depth, tiltDeg) per club type. Driver/wood/hybrid
// share the "rounded" family (rendered as a RoundedBox -- a smooth,
// rounded-edge box reads as a modern clubhead far better than a plain
// ellipsoid) and step down in size and height from driver to wood, with
// hybrid further reduced specifically in depth relative to wood, matching
// how those three actually differ in real equipment. Iron and wedge share
// the "blade" family (a thin flat box); wedge is a touch thicker and tilted
// back slightly to read as a higher-lofted, more open face than the iron.
const BASE_HEAD_SHAPES: Record<ClubType, HeadShape> = {
  driver: { family: "rounded", width: 4.6, height: 2.7, depth: 3.3, tiltDeg: 0 },
  wood: { family: "rounded", width: 3.1, height: 1.7, depth: 2.6, tiltDeg: 0 },
  hybrid: { family: "rounded", width: 2.7, height: 1.7, depth: 1.8, tiltDeg: 0 },
  iron: { family: "blade", width: 0.55, height: 2.15, depth: 1.55, tiltDeg: 0 },
  wedge: { family: "blade", width: 0.68, height: 2.05, depth: 1.6, tiltDeg: 18 },
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
    family: base.family,
    width: base.width * scale,
    height: base.height * scale,
    depth: base.depth * scale,
    tiltDeg: base.tiltDeg,
  };
}
