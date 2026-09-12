import type { HeadMassProperties } from "../api/types";
import { NumberField } from "./NumberField";

interface Props {
  value: HeadMassProperties;
  massFromClub: number;
  onChange: (value: HeadMassProperties) => void;
}

/**
 * The head properties the impact model needs that the club spec does not
 * already carry: where the centre of mass sits, how the head resists
 * twisting, and how big the face is.
 *
 * Mass is NOT edited here -- it comes from the club specification above, so
 * there is one head mass in the app rather than two that can disagree.
 */
export function HeadPropertiesForm({ value, massFromClub, onChange }: Props) {
  const set = <K extends keyof HeadMassProperties>(key: K, next: HeadMassProperties[K]) =>
    onChange({ ...value, [key]: next });

  return (
    <div className="panel head-form">
      <h3>Head mass properties</h3>
      <p className="hint">
        From Fusion: <strong>Inspect → Physical Properties</strong>, with a coordinate
        system at the <strong>centre of the face</strong> — x toward the <strong>heel</strong>,
        y toward the <strong>crown</strong>, z along the <strong>outward face normal</strong>.
        Make sure the dialog reads <em>at centre of mass</em>.
      </p>

      <p className="hint hint--warn">
        Fusion usually reports inertia in <strong>kg·mm²</strong>, and 1&nbsp;kg·mm² = 10&nbsp;g·cm².
        A driver around 4500&nbsp;g·cm² shows there as ~450. Check the conformance
        readout below after entering — it catches that factor of ten immediately.
      </p>

      <dl className="results results--compact">
        <dt>Head mass</dt>
        <dd>{massFromClub.toFixed(0)} g <em>(from the club spec)</em></dd>
      </dl>

      <fieldset>
        <legend>Centre of gravity</legend>
        <div className="field-grid">
          <NumberField label="Toe–heel" unit="mm, + heel" step={0.5}
            value={value.cg_x_mm} onChange={(next) => set("cg_x_mm", next)} />
          <NumberField label="Height" unit="mm, + crown" step={0.5}
            value={value.cg_y_mm} onChange={(next) => set("cg_y_mm", next)} />
          <NumberField label="Depth" unit="mm, negative" step={1}
            value={value.cg_z_mm} onChange={(next) => set("cg_z_mm", next)} />
        </div>
      </fieldset>

      <fieldset>
        <legend>Inertia tensor about the CG (g·cm²)</legend>
        <div className="field-grid">
          <NumberField label="Ixx" unit="toe–heel axis" step={100}
            value={value.i_xx_g_cm2} onChange={(next) => set("i_xx_g_cm2", next)} />
          <NumberField label="Iyy" unit="sole–crown axis" step={100}
            value={value.i_yy_g_cm2} onChange={(next) => set("i_yy_g_cm2", next)} />
          <NumberField label="Izz" unit="face normal" step={100}
            value={value.i_zz_g_cm2} onChange={(next) => set("i_zz_g_cm2", next)} />
          <NumberField label="Ixy" unit="product" step={50}
            value={value.i_xy_g_cm2} onChange={(next) => set("i_xy_g_cm2", next)} />
          <NumberField label="Ixz" unit="product" step={50}
            value={value.i_xz_g_cm2} onChange={(next) => set("i_xz_g_cm2", next)} />
          <NumberField label="Iyz" unit="product" step={50}
            value={value.i_yz_g_cm2} onChange={(next) => set("i_yz_g_cm2", next)} />
        </div>
        <p className="hint">
          Six numbers, not nine — a real inertia tensor is symmetric. Leave the
          products at zero if you do not have them.
        </p>
      </fieldset>

      <fieldset>
        <legend>Face outline</legend>
        <div className="field-grid">
          <NumberField label="Half-width" unit="mm, centre to toe" step={1}
            value={value.face_half_width_mm} onChange={(next) => set("face_half_width_mm", next)} />
          <NumberField label="Half-height" unit="mm, centre to crown" step={1}
            value={value.face_half_height_mm} onChange={(next) => set("face_half_height_mm", next)} />
          <label className="field">
            <span>Shape</span>
            <select value={value.face_shape}
              onChange={(event) => set("face_shape", event.target.value as "ellipse" | "rectangle")}>
              <option value="ellipse">Ellipse</option>
              <option value="rectangle">Rectangle</option>
            </select>
          </label>
          <label className="field field--check">
            <input type="checkbox" checked={value.face_outline_is_measured}
              onChange={(event) => set("face_outline_is_measured", event.target.checked)} />
            <span>Outline measured from real geometry</span>
          </label>
        </div>
        <p className="hint">
          The forgiving-area number is only as good as this outline. Until it is
          measured, every area on the map is labelled as assumed.
        </p>
      </fieldset>
    </div>
  );
}
