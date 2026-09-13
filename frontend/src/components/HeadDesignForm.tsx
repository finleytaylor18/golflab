import { useEffect, useState } from "react";
import type { HeadDesign, PointMass, DesignResult } from "../api/types";
import { getHeadDesign, ApiError } from "../api/client";
import { useDebouncedValue } from "../api/useDebouncedValue";
import { NumberField } from "./NumberField";

interface Props {
  value: HeadDesign;
  onChange: (value: HeadDesign) => void;
  /** The derived head, or null while invalid / loading. */
  onDerived: (result: DesignResult | null) => void;
}

/**
 * A head as a designer thinks of it: a thin ellipsoidal shell cut at the
 * face plane, a face plate, a hosel and some weights, each with a mass.
 *
 * Every edit re-derives the head after a short debounce -- the server
 * integrates ~130k triangles in milliseconds -- so the CG, the tensor and the
 * per-part breakdown update as you type. Masses, not thicknesses: the total
 * is what a designer can check against a real head, and no material density
 * has to be assumed.
 */
export function HeadDesignForm({ value, onChange, onDerived }: Props) {
  const debounced = useDebouncedValue(value, 350);
  const [result, setResult] = useState<DesignResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    getHeadDesign(debounced)
      .then((derived) => {
        if (cancelled) return;
        setResult(derived);
        setError(null);
        onDerived(derived);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setResult(null);
        setError(err instanceof ApiError ? err.message : "Could not reach the GolfLab API. Is it running on :8000?");
        onDerived(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
    // onDerived is a setter from the parent; re-running on its identity would loop.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debounced]);

  const set = <K extends keyof HeadDesign>(key: K, next: HeadDesign[K]) =>
    onChange({ ...value, [key]: next });

  const setHosel = (patch: Partial<PointMass>) => set("hosel", { ...value.hosel, ...patch });

  const setWeight = (index: number, patch: Partial<PointMass>) =>
    set("weights", value.weights.map((w, i) => (i === index ? { ...w, ...patch } : w)));

  const removeWeight = (index: number) =>
    set("weights", value.weights.filter((_, i) => i !== index));

  const addWeight = () =>
    set("weights", [
      ...value.weights,
      { name: `weight ${value.weights.length + 1}`, mass_g: 10, toe_mm: 0, crown_mm: -10, back_mm: 60 },
    ]);

  const totalMass =
    value.crown_mass_g + value.sole_mass_g + value.face_mass_g + value.hosel.mass_g +
    value.weights.reduce((sum, w) => sum + w.mass_g, 0);

  return (
    <div className="panel head-form">
      <h3>Parametric head design</h3>
      <p className="hint">
        An idealised head: a thin <strong>ellipsoidal shell</strong> cut at the face plane,
        a flat <strong>face plate</strong> filling the opening, a <strong>hosel</strong> and
        <strong> weights</strong> as point masses. The tensor is derived from what you type.
        The shape is the estimate — trends and ratios are trustworthy, absolute values only
        as far as an ellipsoid resembles your head. Not a product.
      </p>

      <label className="field">
        <span>Design name</span>
        <input value={value.name} onChange={(e) => set("name", e.target.value)} />
      </label>

      <fieldset>
        <legend>Shell (ellipsoid semi-axes)</legend>
        <div className="field-grid">
          <NumberField label="Half-width" unit="mm, centre → heel" step={1}
            value={value.half_width_mm} onChange={(v) => set("half_width_mm", v)} />
          <NumberField label="Half-height" unit="mm, centre → crown" step={1}
            value={value.half_height_mm} onChange={(v) => set("half_height_mm", v)} />
          <NumberField label="Half-depth" unit="mm, centre → back" step={1}
            value={value.half_depth_mm} onChange={(v) => set("half_depth_mm", v)} />
          <NumberField label="Face width" unit="mm, where the face cuts the shell" step={1}
            value={value.face_width_mm} onChange={(v) => set("face_width_mm", v)} />
        </div>
        <p className="hint">
          Rules limits for woods: heel–toe ≤ 127 mm, sole–crown ≤ 71.12 mm, heel–toe longer
          than face–back, volume ≤ 460 cc. Reported below, never enforced.
        </p>
      </fieldset>

      <fieldset>
        <legend>Mass budget (g) — total {totalMass.toFixed(0)} g</legend>
        <div className="field-grid">
          <NumberField label="Crown shell" unit="g, above centre" step={1}
            value={value.crown_mass_g} onChange={(v) => set("crown_mass_g", v)} />
          <NumberField label="Sole shell" unit="g, below centre" step={1}
            value={value.sole_mass_g} onChange={(v) => set("sole_mass_g", v)} />
          <NumberField label="Face plate" unit="g" step={1}
            value={value.face_mass_g} onChange={(v) => set("face_mass_g", v)} />
        </div>
      </fieldset>

      <fieldset>
        <legend>Hosel</legend>
        <div className="field-grid">
          <NumberField label="Mass" unit="g" step={1}
            value={value.hosel.mass_g} onChange={(v) => setHosel({ mass_g: v })} />
          <NumberField label="Toward toe" unit="mm, − = heel" step={1}
            value={value.hosel.toe_mm} onChange={(v) => setHosel({ toe_mm: v })} />
          <NumberField label="Toward crown" unit="mm, − = sole" step={1}
            value={value.hosel.crown_mm} onChange={(v) => setHosel({ crown_mm: v })} />
          <NumberField label="Back from face" unit="mm" step={1}
            value={value.hosel.back_mm} onChange={(v) => setHosel({ back_mm: v })} />
        </div>
      </fieldset>

      <fieldset>
        <legend>Weights</legend>
        {value.weights.map((weight, index) => (
          <div className="weight-row" key={index}>
            <label className="field">
              <span>Name</span>
              <input value={weight.name} onChange={(e) => setWeight(index, { name: e.target.value })} />
            </label>
            <NumberField label="Mass" unit="g" step={1}
              value={weight.mass_g} onChange={(v) => setWeight(index, { mass_g: v })} />
            <NumberField label="Toward toe" unit="mm" step={1}
              value={weight.toe_mm} onChange={(v) => setWeight(index, { toe_mm: v })} />
            <NumberField label="Toward crown" unit="mm" step={1}
              value={weight.crown_mm} onChange={(v) => setWeight(index, { crown_mm: v })} />
            <NumberField label="Back" unit="mm" step={1}
              value={weight.back_mm} onChange={(v) => setWeight(index, { back_mm: v })} />
            <button type="button" className="tab" onClick={() => removeWeight(index)}>Remove</button>
          </div>
        ))}
        <button type="button" className="tab" onClick={addWeight}>Add a weight</button>
      </fieldset>

      {error && <p className="error">{error}</p>}

      {result && (
        <div className={loading ? "stale" : undefined}>
          <dl className="results results--compact">
            <dt>Derived mass</dt>
            <dd>{result.mass_g.toFixed(1)} g</dd>
            <dt>Centre of gravity</dt>
            <dd>
              {(-result.cg_mm[0]).toFixed(1)} mm toward toe, {result.cg_mm[1].toFixed(1)} mm up,{" "}
              {result.cg_depth_mm.toFixed(1)} mm deep
            </dd>
            <dt>Sweet spot</dt>
            <dd>
              {(-result.sweet_spot_mm[0]).toFixed(1)} mm toward toe, {result.sweet_spot_mm[1].toFixed(1)} mm up
            </dd>
            <dt>Inertia about the CG</dt>
            <dd>
              Ixx {result.inertia_g_cm2[0][0].toFixed(0)} · Iyy {result.inertia_g_cm2[1][1].toFixed(0)} ·
              Izz {result.inertia_g_cm2[2][2].toFixed(0)} g·cm²
            </dd>
          </dl>

          <table className="breakdown">
            <thead>
              <tr><th>Part</th><th>Mass</th><th>of mass</th><th>of Ixx</th><th>of Iyy</th></tr>
            </thead>
            <tbody>
              {result.breakdown.map((part) => (
                <tr key={part.name}>
                  <td>{part.name}</td>
                  <td>{part.mass_g.toFixed(1)} g</td>
                  <td>{(100 * part.mass_share).toFixed(0)} %</td>
                  <td>{(100 * part.ixx_share).toFixed(1)} %</td>
                  <td>{(100 * part.iyy_share).toFixed(1)} %</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="hint">
            Each part's share is its own tensor plus its parallel-axis term about the assembled
            CG — a true partition, so the columns sum to 100 %.
          </p>

          <div className="conformance">
            <strong>Rules:</strong>{" "}
            heel–toe {result.conformance.heel_toe_mm.toFixed(0)} mm ·
            sole–crown {result.conformance.sole_crown_mm.toFixed(0)} mm ·
            face–back {result.conformance.face_to_back_mm.toFixed(0)} mm ·
            volume {result.conformance.volume_cc.toFixed(0)} cc ·
            MOI {result.conformance.rules_frame_moi_g_cm2.toFixed(0)} g·cm² —{" "}
            <span className={result.conformance.conforms ? "ok" : "warn"}>
              {result.conformance.conforms ? "conforming" : "NON-CONFORMING"}
            </span>
            {" "}<em>({result.conformance.citation})</em>
          </div>
          {result.warnings.map((warning) => (
            <p className="caveat caveat--warn" key={warning}>{warning}</p>
          ))}
        </div>
      )}
      {!result && loading && <p className="status">Deriving…</p>}
    </div>
  );
}
