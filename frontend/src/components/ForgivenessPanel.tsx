import { useMemo, useState } from "react";
import type {
  ClubSpecification, SwingProfile, HeadMassProperties,
  ForgivenessMapResult, MapComparisonResult, Grid, MapSettings,
} from "../api/types";
import { DEFAULT_HEAD, DEFAULT_MAP_SETTINGS } from "../api/types";
import { getForgivenessMap, getForgivenessComparison, ApiError } from "../api/client";
import { HeadPropertiesForm } from "./HeadPropertiesForm";
import { ForgivenessHeatmap, type HoverPoint } from "./ForgivenessHeatmap";
import { Spinner } from "./Spinner";
import type { RampName } from "./colourScales";

interface Props {
  club: ClubSpecification;
  swing: SwingProfile;
}

interface MetricDefinition {
  key: string;
  label: string;
  unit: string;
  ramp: RampName;
  diverging: boolean;
  decimals: number;
  pick: (map: ForgivenessMapResult) => Grid;
}

const METRICS: MetricDefinition[] = [
  {
    key: "retention", label: "Ball speed retention", unit: "% of sweet-spot ball speed",
    ramp: "viridis", diverging: false, decimals: 1,
    pick: (map) => map.speed_retention_pct,
  },
  {
    key: "sidespin", label: "Sidespin", unit: "rpm  (+ curves right)",
    ramp: "redBlue", diverging: true, decimals: 0,
    pick: (map) => map.sidespin_rpm,
  },
  {
    key: "backspin", label: "Backspin", unit: "rpm",
    ramp: "plasma", diverging: false, decimals: 0,
    pick: (map) => map.backspin_rpm,
  },
  {
    key: "launch", label: "Launch angle", unit: "degrees",
    ramp: "cividis", diverging: false, decimals: 2,
    pick: (map) => map.launch_angle_deg,
  },
];

const DELTA_METRICS = [
  { key: "retention", label: "Δ ball speed retention", unit: "percentage points", decimals: 2,
    pick: (c: MapComparisonResult) => c.delta_speed_retention_pct },
  { key: "sidespin", label: "Δ sidespin", unit: "rpm", decimals: 0,
    pick: (c: MapComparisonResult) => c.delta_sidespin_rpm },
  { key: "backspin", label: "Δ backspin", unit: "rpm", decimals: 0,
    pick: (c: MapComparisonResult) => c.delta_backspin_rpm },
  { key: "launch", label: "Δ launch angle", unit: "degrees", decimals: 2,
    pick: (c: MapComparisonResult) => c.delta_launch_angle_deg },
];

/**
 * Recompute the forgiving area for a threshold the user is dragging.
 *
 * Done in the browser on purpose. The retention grid is already here, so a
 * threshold change is a scan over ~1600 numbers -- instant, and with no
 * server round trip the slider can drive the contour in real time. The
 * arithmetic deliberately matches ForgivenessMap.forgiving_area_mm2(): count
 * cells and multiply by cell area, rather than fitting a smooth contour that
 * would look more precise than an assumed face outline deserves.
 */
function areaAtThreshold(map: ForgivenessMapResult, threshold: number) {
  const spacing = map.x_mm.length > 1 ? map.x_mm[1] - map.x_mm[0] : 1;
  const cellArea = spacing * spacing;
  let keeping = 0;
  let onFace = 0;
  for (let row = 0; row < map.y_mm.length; row += 1) {
    for (let column = 0; column < map.x_mm.length; column += 1) {
      if (!map.on_face[row][column]) continue;
      onFace += 1;
      const value = map.speed_retention_pct[row][column];
      if (value !== null && value >= threshold) keeping += 1;
    }
  }
  const faceArea = onFace * cellArea;
  return {
    area: keeping * cellArea,
    faceArea,
    fraction: faceArea > 0 ? (keeping * cellArea) / faceArea : 0,
  };
}

export function ForgivenessPanel({ club, swing }: Props) {
  const [head, setHead] = useState<HeadMassProperties>(DEFAULT_HEAD);
  const [settings, setSettings] = useState<MapSettings>(DEFAULT_MAP_SETTINGS);
  const [map, setMap] = useState<ForgivenessMapResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [metricKey, setMetricKey] = useState("retention");
  const [hover, setHover] = useState<HoverPoint | null>(null);
  const [pinned, setPinned] = useState<HoverPoint | null>(null);
  const [showMarkers, setShowMarkers] = useState(true);
  const [showFlags, setShowFlags] = useState(true);
  const [showContour, setShowContour] = useState(true);

  const [baseline, setBaseline] = useState<{ head: HeadMassProperties; label: string } | null>(null);
  const [comparison, setComparison] = useState<MapComparisonResult | null>(null);
  const [comparing, setComparing] = useState(false);

  // The impact model's loft is the angle between the face normal and the
  // direction the head is actually travelling -- not loft against the horizon.
  // With a swing profile in hand that is dynamic loft minus attack angle.
  const conditions = useMemo(() => ({
    clubhead_speed_mph: swing.clubhead_speed,
    loft_deg: swing.dynamic_loft - swing.attack_angle,
  }), [swing.clubhead_speed, swing.dynamic_loft, swing.attack_angle]);

  const headWithClubMass = useMemo(
    () => ({ ...head, mass_g: club.head_mass }),
    [head, club.head_mass],
  );

  async function runMap() {
    setLoading(true);
    setError(null);
    setComparison(null);
    try {
      const result = await getForgivenessMap(headWithClubMass, conditions, settings);
      setMap(result);
      setPinned(null);
    } catch (err) {
      setMap(null);
      setError(err instanceof ApiError ? err.message : "Could not reach the GolfLab API. Is it running on :8000?");
    } finally {
      setLoading(false);
    }
  }

  async function runComparison() {
    if (!baseline) return;
    setComparing(true);
    setError(null);
    try {
      const result = await getForgivenessComparison(
        baseline.label, baseline.head, "current head", headWithClubMass,
        conditions, settings,
      );
      setComparison(result);
    } catch (err) {
      setComparison(null);
      setError(err instanceof ApiError ? err.message : "Could not reach the GolfLab API.");
    } finally {
      setComparing(false);
    }
  }

  const metric = METRICS.find((entry) => entry.key === metricKey) ?? METRICS[0];
  const deltaMetric = DELTA_METRICS.find((entry) => entry.key === metricKey) ?? DELTA_METRICS[0];
  const readoutPoint = hover ?? pinned;
  const liveArea = map ? areaAtThreshold(map, settings.retention_threshold_pct) : null;

  return (
    <div className="panel panel--forgiveness">
      <div className="simulation-header">
        <h2>Impact model &amp; forgiveness map</h2>
        <button type="button" onClick={runMap} disabled={loading}>
          {loading && <span className="button-spinner" aria-hidden="true" />}
          {loading ? "Sweeping…" : map ? "Re-run sweep" : "Run sweep"}
        </button>
      </div>

      <p className="status">
        Sweeps the strike location across the face and solves a rigid-body impact at
        every point. Using <strong>{conditions.clubhead_speed_mph.toFixed(1)} mph</strong> and
        a delivered loft of <strong>{conditions.loft_deg.toFixed(1)}°</strong> (dynamic
        loft {swing.dynamic_loft}° − attack angle {swing.attack_angle}°, because the
        impact depends on loft relative to the head's <em>path</em>, not to the horizon).
      </p>

      <HeadPropertiesForm value={head} massFromClub={club.head_mass} onChange={setHead} />

      {error && <p className="error">{error}</p>}
      {!map && loading && <Spinner label="Solving every point on the face…" />}
      {!map && !loading && !error && (
        <p className="status">Enter the head's mass properties, then run the sweep.</p>
      )}

      {map && (
        <div className={loading ? "stale" : undefined}>
          {/* Hidden while comparing: this conformance figure belongs to the
              head that was swept, and in comparison mode the form may have
              moved on to a different one. Showing it there would label the
              picture with the wrong head's number. */}
          {!comparison && (
            <div className="conformance">
              <strong>Rules-frame MOI:</strong>{" "}
              {map.conformance.rules_frame_moi_g_cm2.toFixed(0)} g·cm²
              {" — "}
              <span className={map.conformance.conforms ? "ok" : "warn"}>
                {map.conformance.conforms ? "conforming" : "NON-CONFORMING"}
              </span>
              {" "}(limit {map.conformance.limit_g_cm2.toFixed(0)} + 100 tolerance).{" "}
              <em>{map.conformance.citation}</em>
            </div>
          )}

          <div className="metric-tabs">
            {(comparison ? DELTA_METRICS : METRICS).map((entry) => (
              <button
                key={entry.key}
                type="button"
                className={entry.key === metricKey ? "tab tab--active" : "tab"}
                onClick={() => setMetricKey(entry.key)}
              >
                {entry.label}
              </button>
            ))}
          </div>

          <div className="map-layout">
            <div className="map-canvas-wrap">
              {comparison ? (
                <ForgivenessHeatmap
                  xMm={comparison.x_mm}
                  yMm={comparison.y_mm}
                  values={deltaMetric.pick(comparison)}
                  onFace={comparison.on_face}
                  ramp="redBlue"
                  diverging
                  unit={deltaMetric.unit}
                  sweetSpotMm={map.sweet_spot_mm}
                  faceCentreMm={map.face_centre_mm}
                  showFlags={false}
                  showMarkers={showMarkers}
                  hover={hover} pinned={pinned}
                  onHover={setHover} onPin={setPinned}
                />
              ) : (
                <ForgivenessHeatmap
                  xMm={map.x_mm}
                  yMm={map.y_mm}
                  values={metric.pick(map)}
                  onFace={map.on_face}
                  ramp={metric.ramp}
                  diverging={metric.diverging}
                  unit={metric.unit}
                  contourAtLeast={
                    showContour && metric.key === "retention"
                      ? settings.retention_threshold_pct
                      : null
                  }
                  frictionFlags={map.exceeds_friction}
                  topspinFlags={map.backspin_reversed}
                  sweetSpotMm={map.sweet_spot_mm}
                  faceCentreMm={map.face_centre_mm}
                  showFlags={showFlags}
                  showMarkers={showMarkers}
                  hover={hover} pinned={pinned}
                  onHover={setHover} onPin={setPinned}
                />
              )}

              <div className="map-legend">
                <span><b>✳</b> sweet spot</span>
                <span><b>✕</b> face centre</span>
                <span><b>·</b> needs more friction than the sourced μ</span>
                <span><b>○</b> topspin — flat-face limit</span>
                <span className="map-legend-hint">Hover to read a strike · click to pin it</span>
              </div>
            </div>

            <div className="map-readout">
              <h4>
                {readoutPoint
                  ? `Strike at ${(-readoutPoint.xMm).toFixed(0)} mm ${readoutPoint.xMm <= 0 ? "toward toe" : "toward heel"}, ${readoutPoint.yMm.toFixed(0)} mm ${readoutPoint.yMm >= 0 ? "up" : "down"}`
                  : "Hover the map"}
              </h4>
              {readoutPoint ? (
                <dl className="results results--compact">
                  <dt>Ball speed</dt>
                  <dd>{cell(map.ball_speed_mph, readoutPoint, 1)} mph</dd>
                  <dt>Retention</dt>
                  <dd>{cell(map.speed_retention_pct, readoutPoint, 1)} %</dd>
                  <dt>Launch angle</dt>
                  <dd>{cell(map.launch_angle_deg, readoutPoint, 2)}°</dd>
                  <dt>Backspin</dt>
                  <dd>{cell(map.backspin_rpm, readoutPoint, 0)} rpm</dd>
                  <dt>Sidespin</dt>
                  <dd>{cell(map.sidespin_rpm, readoutPoint, 0)} rpm</dd>
                  <dt>Spin axis</dt>
                  <dd>
                    {map.spin_axis_deg[readoutPoint.row][readoutPoint.column] === null
                      ? "undefined (topspin)"
                      : `${cell(map.spin_axis_deg, readoutPoint, 1)}°`}
                  </dd>
                  <dt>Friction used</dt>
                  <dd>
                    {cell(map.required_friction, readoutPoint, 3)}
                    {map.exceeds_friction[readoutPoint.row][readoutPoint.column] && (
                      <span className="warn"> — exceeds sourced μ</span>
                    )}
                  </dd>
                  {comparison && (
                    <>
                      <dt>{deltaMetric.label}</dt>
                      <dd>{cell(deltaMetric.pick(comparison), readoutPoint, deltaMetric.decimals)}</dd>
                    </>
                  )}
                </dl>
              ) : (
                <p className="status">
                  Move the pointer over the face to read every launch condition at that
                  strike. Click to pin one while you change the head.
                </p>
              )}
            </div>
          </div>

          <div className="map-controls">
            <label className="field field--slider" hidden={comparison !== null}>
              <span>
                Retention threshold <em>({settings.retention_threshold_pct.toFixed(0)}%)</em>
              </span>
              <input
                type="range" min={80} max={100} step={0.5}
                value={settings.retention_threshold_pct}
                onChange={(event) =>
                  setSettings({ ...settings, retention_threshold_pct: Number(event.target.value) })
                }
              />
            </label>

            <label className="field">
              <span>Grid spacing <em>(mm)</em></span>
              <select
                value={settings.spacing_mm}
                onChange={(event) =>
                  setSettings({ ...settings, spacing_mm: Number(event.target.value) })
                }
              >
                <option value={1}>1 — fine</option>
                <option value={2}>2 — default</option>
                <option value={2.5}>2.5</option>
                <option value={5}>5 — coarse</option>
              </select>
            </label>

            <div className="toggles">
              <label><input type="checkbox" checked={showMarkers}
                onChange={(event) => setShowMarkers(event.target.checked)} /> Markers</label>
              <label><input type="checkbox" checked={showFlags}
                onChange={(event) => setShowFlags(event.target.checked)} /> Model-limit flags</label>
              <label><input type="checkbox" checked={showContour}
                onChange={(event) => setShowContour(event.target.checked)} /> Threshold contour</label>
            </div>
          </div>

          <p className="hint">
            {comparison
              ? "Comparison areas are quoted at the threshold used when Compare was pressed — the difference map carries deltas, not each head's own retention grid, so the threshold cannot be re-applied here without another request."
              : "The threshold slider and its contour update instantly — the grid is already in the browser, so no re-run is needed. Changing the grid spacing does need a re-run."}
          </p>

          {comparison && (
            <dl className="results results--summary">
              <dt>Area keeping ≥ {comparison.summary_a.threshold_pct.toFixed(0)}% — {comparison.name_a}</dt>
              <dd>
                {comparison.summary_a.forgiving_area_mm2.toFixed(0)} mm²
                {" "}({(comparison.summary_a.forgiving_area_fraction * 100).toFixed(0)}%)
              </dd>
              <dt>Area keeping ≥ {comparison.summary_b.threshold_pct.toFixed(0)}% — {comparison.name_b}</dt>
              <dd>
                {comparison.summary_b.forgiving_area_mm2.toFixed(0)} mm²
                {" "}({(comparison.summary_b.forgiving_area_fraction * 100).toFixed(0)}%)
              </dd>
              <dt>Difference</dt>
              <dd>
                {(comparison.summary_b.forgiving_area_mm2
                  - comparison.summary_a.forgiving_area_mm2 >= 0 ? "+" : "")}
                {(comparison.summary_b.forgiving_area_mm2
                  - comparison.summary_a.forgiving_area_mm2).toFixed(0)} mm²
              </dd>
              <dt>Worst retention</dt>
              <dd>
                {comparison.summary_a.worst_retention_pct.toFixed(1)}% → {" "}
                {comparison.summary_b.worst_retention_pct.toFixed(1)}%
              </dd>
              <dt>Largest sidespin</dt>
              <dd>
                {comparison.summary_a.max_abs_sidespin_rpm.toFixed(0)} → {" "}
                {comparison.summary_b.max_abs_sidespin_rpm.toFixed(0)} rpm
              </dd>
            </dl>
          )}

          {!comparison && liveArea && (
            <dl className="results results--summary">
              <dt>Sweet spot</dt>
              <dd>
                {(-map.sweet_spot_mm[0]).toFixed(1)} mm toward toe,{" "}
                {map.sweet_spot_mm[1].toFixed(1)} mm up
              </dd>
              <dt>Sweet-spot ball speed</dt>
              <dd>{map.summary.sweet_spot_ball_speed_mph.toFixed(1)} mph</dd>
              <dt>Area keeping ≥ {settings.retention_threshold_pct.toFixed(0)}%</dt>
              <dd>
                {liveArea.area.toFixed(0)} mm² of {liveArea.faceArea.toFixed(0)} mm²
                {" "}({(liveArea.fraction * 100).toFixed(0)}%)
              </dd>
              <dt>Worst retention on the face</dt>
              <dd>{map.summary.worst_retention_pct.toFixed(1)} %</dd>
              <dt>Backspin range</dt>
              <dd>
                {map.summary.backspin_range_rpm[0].toFixed(0)} to{" "}
                {map.summary.backspin_range_rpm[1].toFixed(0)} rpm
              </dd>
              <dt>Largest sidespin</dt>
              <dd>{map.summary.max_abs_sidespin_rpm.toFixed(0)} rpm</dd>
              <dt>Face outline</dt>
              <dd>{map.face_description}</dd>
            </dl>
          )}

          <div className="caveats">
            <p className="caveat">
              The <strong>{settings.retention_threshold_pct.toFixed(0)}% threshold is a chosen
              setting, not an industry standard.</strong> No source read for this project
              defines a forgiveness area, so the number only means anything alongside the
              threshold that produced it.
            </p>
            <p className="caveat caveat--warn">
              <strong>The v1 face is flat — no bulge or roll.</strong> Real face curvature exists
              to counteract the gear effect shown here, so curvature is overstated toward the
              rim. Trust the centre of the map; treat the edges as an upper bound.
            </p>
            {map.summary.points_with_reversed_backspin > 0 && (
              <p className="caveat caveat--warn">
                {map.summary.points_with_reversed_backspin} grid points show
                <strong> topspin</strong> — the flat-face assumption has broken down there,
                and their spin axis is left undefined rather than reported as an angle.
              </p>
            )}
            {map.summary.points_needing_more_friction > 0 && (
              <p className="caveat caveat--warn">
                {map.summary.points_needing_more_friction} grid points need more friction
                than the sourced coefficient allows — the model is extrapolating there.
              </p>
            )}
            <p className="caveat">
              Ball: {map.ball_description}. One COR is applied everywhere on the face, so a
              real head loses <em>more</em> ball speed off-centre than this shows.
            </p>
          </div>

          <div className="compare-row">
            <button type="button" onClick={() => {
              setBaseline({ head: headWithClubMass, label: "baseline" });
              setComparison(null);
            }}>
              Set current head as baseline
            </button>
            <button type="button" disabled={!baseline || comparing} onClick={runComparison}>
              {comparing ? "Comparing…" : "Compare with baseline"}
            </button>
            {comparison && (
              <button type="button" onClick={() => setComparison(null)}>
                Back to single map
              </button>
            )}
            {baseline && !comparison && (
              <span className="status">
                Baseline stored. Change the head above, then compare.
              </span>
            )}
            {comparison && (
              <span className="status">
                Showing <strong>{comparison.name_b} − {comparison.name_a}</strong>; red means
                the current head is higher. Sign matches the project's existing delta
                convention.
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function cell(grid: Grid, point: HoverPoint, decimals: number): string {
  const value = grid[point.row]?.[point.column];
  return value === null || value === undefined ? "—" : value.toFixed(decimals);
}
