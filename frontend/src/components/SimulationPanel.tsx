import { useState, lazy, Suspense } from "react";
import type { ClubSpecification, SwingProfile, BallFlightResult } from "../api/types";
import { getBallFlight, ApiError } from "../api/client";
import { Spinner } from "./Spinner";

// recharts is only needed once a simulation has actually run -- keeping it
// out of the initial bundle means the page paints without waiting on it.
const TrajectoryCharts = lazy(() =>
  import("./TrajectoryCharts").then((m) => ({ default: m.TrajectoryCharts })),
);

interface Props {
  club: ClubSpecification;
  swing: SwingProfile;
}

export function SimulationPanel({ club, swing }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BallFlightResult | null>(null);

  async function runSimulation() {
    setLoading(true);
    setError(null);
    try {
      const flight = await getBallFlight(club, swing);
      setResult(flight);
    } catch (err) {
      setResult(null);
      setError(err instanceof ApiError ? err.message : "Could not reach the GolfLab API. Is it running on :8000?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="panel panel--simulation">
      <div className="simulation-header">
        <h2>Ball flight simulation</h2>
        <button type="button" onClick={runSimulation} disabled={loading}>
          {loading && <span className="button-spinner" aria-hidden="true" />}
          {loading ? "Simulating…" : "Run simulation"}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      {result && (
        <div className={loading ? "stale" : undefined}>
          <dl className="results results--simulation">
            <dt>Carry distance</dt>
            <dd>{result.trajectory.carry_distance.toFixed(1)} yd</dd>
            <dt>Peak height</dt>
            <dd>{result.trajectory.peak_height.toFixed(1)} yd</dd>
            <dt>Lateral deviation</dt>
            <dd>{result.trajectory.lateral_deviation.toFixed(1)} yd</dd>
            <dt>Shot shape</dt>
            <dd className="shot-shape">{result.trajectory.shot_shape}</dd>
            <dt>Ball speed</dt>
            <dd>{result.launch_conditions.ball_speed.toFixed(1)} mph</dd>
            <dt>Launch angle</dt>
            <dd>{result.launch_conditions.launch_angle.toFixed(1)}°</dd>
            <dt>Backspin</dt>
            <dd>{result.launch_conditions.backspin.toFixed(0)} rpm</dd>
            <dt>Sidespin</dt>
            <dd>{result.launch_conditions.sidespin.toFixed(0)} rpm</dd>
          </dl>

          <Suspense fallback={<Spinner label="Loading charts…" />}>
            <TrajectoryCharts points={result.trajectory.points} />
          </Suspense>
        </div>
      )}

      {!result && !error && !loading && (
        <p className="status">Set up a club and swing profile above, then run a simulation.</p>
      )}
      {!result && loading && <Spinner label="Running simulation…" />}
    </div>
  );
}
