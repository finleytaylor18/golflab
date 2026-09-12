import type {
  ClubSpecification,
  SwingProfile,
  SwingWeightResult,
  MoiResult,
  BalancePointResult,
  BallFlightResult,
  HeadMassProperties,
  ImpactConditions,
  MapSettings,
  ForgivenessMapResult,
  MapComparisonResult,
  ImpactResult,
} from "./types";

// Relative -- in production this app is served by the same FastAPI process
// it's calling (see main.py's StaticFiles mount), and in dev, vite.config.ts
// proxies these paths to the backend, so there's no cross-origin request in
// either case and no base URL to hardcode.
class ApiError extends Error {}

async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(payload.detail ?? "Request failed");
  }
  return response.json();
}

export function getSwingWeight(club: ClubSpecification): Promise<SwingWeightResult> {
  return post("/calculations/swing-weight", club);
}

export function getMoi(club: ClubSpecification): Promise<MoiResult> {
  return post("/calculations/moi", club);
}

export function getBalancePoint(club: ClubSpecification): Promise<BalancePointResult> {
  return post("/calculations/balance-point", club);
}

export function getBallFlight(club: ClubSpecification, swing: SwingProfile): Promise<BallFlightResult> {
  return post("/calculations/ball-flight", { club, swing });
}

export function getForgivenessMap(
  head: HeadMassProperties,
  conditions: ImpactConditions,
  settings: MapSettings,
): Promise<ForgivenessMapResult> {
  return post("/calculations/forgiveness-map", { head, conditions, settings });
}

export function getForgivenessComparison(
  nameA: string,
  headA: HeadMassProperties,
  nameB: string,
  headB: HeadMassProperties,
  conditions: ImpactConditions,
  settings: MapSettings,
): Promise<MapComparisonResult> {
  return post("/calculations/forgiveness-compare", {
    name_a: nameA,
    head_a: headA,
    name_b: nameB,
    head_b: headB,
    conditions,
    settings,
  });
}

export function getImpact(
  head: HeadMassProperties,
  conditions: ImpactConditions,
  strikeToeMm: number,
  strikeCrownMm: number,
): Promise<ImpactResult> {
  return post("/calculations/impact", {
    head,
    conditions,
    strike_toe_mm: strikeToeMm,
    strike_crown_mm: strikeCrownMm,
  });
}

export { ApiError };
