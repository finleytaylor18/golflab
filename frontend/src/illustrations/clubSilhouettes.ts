import type { ClubType } from "../api/types";

// Shared anchor points for the grip+shaft skeleton every club silhouette
// attaches to. All head paths below are drawn in this same coordinate
// space, starting/ending at HOSEL_POINT, so swapping club_type only swaps
// the head shape without moving the shaft.
export const VIEW_WIDTH = 240;
export const VIEW_HEIGHT = 400;
export const GRIP_TOP = { x: 44, y: 10 };
export const GRIP_BOTTOM = { x: 67, y: 78 };
export const HOSEL_POINT = { x: 150, y: 320 };
export const GROUND_Y = 358;

// Hand-drawn, unbranded side-profile (address-view) silhouettes -- one
// fixed path per club type. Purely aesthetic: these don't respond to any
// input beyond the overall/head scale applied in ClubIllustration.tsx.
export const HEAD_PATHS: Record<ClubType, string> = {
  // Large, asymmetric rounded head: a near-flat face at the hosel side,
  // sweeping up into a tall crown and a big rounded back -- the modern
  // big-headed driver silhouette, not a symmetric blob.
  driver:
    "M150,320 L152,295 C160,272 185,261 213,262 C242,263 251,285 249,312 C248,335 234,353 208,358 L158,358 C151,354 148,338 150,320 Z",
  // Same flat-face/rounded-back family as the driver, scaled down and
  // shallower (less crown height) -- a fairway wood.
  wood:
    "M150,323 L151,305 C158,288 175,281 197,283 C217,285 223,301 221,319 C220,335 207,347 188,354 L158,357 C151,354 147,338 150,323 Z",
  // Same family again, smaller and more compact than the wood in every
  // dimension -- reads as a small rounded head, not a scaled-down driver.
  hybrid:
    "M150,325 L151,311 C156,297 169,291 184,293 C199,295 205,306 203,320 C202,335 192,344 177,352 L158,355 C152,352 148,338 150,325 Z",
  // Flat blade: a straight angled topline from the hosel to a rounded toe,
  // a straight back edge, and a flat sole -- the classic iron silhouette.
  // Deliberately angular (mostly straight lines), not rounded, to read as
  // a distinct family from the driver/wood/hybrid heads above.
  iron:
    "M148,318 L206,294 C213,292 216,297 215,304 L209,343 C208,352 200,358 188,358 L154,358 L148,318 Z",
  // Same blade family as the iron (straight topline/back edge), but a
  // shallower topline angle (a more open-looking face) and a visibly
  // thicker, rounded sole -- the wedge's bounce.
  wedge:
    "M148,320 L196,300 C204,297 209,302 209,309 L204,340 C202,352 193,360 178,360 L152,358 L148,320 Z",
};
