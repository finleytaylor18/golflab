// Colour ramps matching the matplotlib panels in forgiveness_diagram.py, so
// the web view and a saved figure of the same map read the same way.
//
// Approximated from the matplotlib colormaps with a handful of stops and
// linear interpolation between them. That is plenty for a heat map that is
// read for shape and gradient rather than for absolute colour values -- and
// it avoids pulling in a colour library for four gradients.

type Stop = [number, number, number];

const VIRIDIS: Stop[] = [
  [68, 1, 84], [72, 40, 120], [62, 74, 137], [49, 104, 142],
  [38, 130, 142], [31, 158, 137], [53, 183, 121], [109, 205, 89],
  [180, 222, 44], [253, 231, 37],
];

const PLASMA: Stop[] = [
  [13, 8, 135], [75, 3, 161], [125, 3, 168], [168, 34, 150],
  [203, 70, 121], [229, 107, 93], [248, 148, 65], [253, 195, 40],
  [240, 249, 33],
];

const CIVIDIS: Stop[] = [
  [0, 32, 76], [0, 57, 108], [42, 79, 110], [70, 100, 111],
  [95, 119, 112], [123, 140, 111], [155, 162, 106], [192, 186, 94],
  [232, 213, 73], [253, 231, 55],
];

// Diverging: a deep blue through near-white to a deep red. Must be symmetric
// about its midpoint or the colour would misrepresent which side of zero a
// value sits on.
const RED_BLUE: Stop[] = [
  [5, 48, 97], [33, 102, 172], [67, 147, 195], [146, 197, 222],
  [209, 229, 240], [247, 247, 247], [253, 219, 199], [244, 165, 130],
  [214, 96, 77], [178, 24, 43], [103, 0, 31],
];

export const RAMPS = {
  viridis: VIRIDIS,
  plasma: PLASMA,
  cividis: CIVIDIS,
  redBlue: RED_BLUE,
} as const;

export type RampName = keyof typeof RAMPS;

/** Sample a ramp at t in [0, 1]. Values outside are clamped to the ends. */
export function sampleRamp(name: RampName, t: number): string {
  const stops = RAMPS[name];
  const clamped = Number.isFinite(t) ? Math.min(1, Math.max(0, t)) : 0;
  const scaled = clamped * (stops.length - 1);
  const lower = Math.floor(scaled);
  const upper = Math.min(stops.length - 1, lower + 1);
  const blend = scaled - lower;

  const [r1, g1, b1] = stops[lower];
  const [r2, g2, b2] = stops[upper];
  const mix = (a: number, b: number) => Math.round(a + (b - a) * blend);
  return `rgb(${mix(r1, r2)}, ${mix(g1, g2)}, ${mix(b1, b2)})`;
}

/** CSS gradient for a colour-bar legend. */
export function rampGradient(name: RampName): string {
  const steps = 12;
  const colours = Array.from({ length: steps + 1 }, (_, index) =>
    sampleRamp(name, index / steps),
  );
  return `linear-gradient(to right, ${colours.join(", ")})`;
}
