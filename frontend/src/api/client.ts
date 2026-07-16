import type {
  ClubSpecification,
  SwingProfile,
  SwingWeightResult,
  MoiResult,
  BalancePointResult,
  BallFlightResult,
} from "./types";

const API_BASE = "http://localhost:8000";

class ApiError extends Error {}

async function post<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
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
