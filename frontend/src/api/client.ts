import type {
  ClubSpecification,
  SwingProfile,
  SwingWeightResult,
  MoiResult,
  BalancePointResult,
  BallFlightResult,
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

export { ApiError };
