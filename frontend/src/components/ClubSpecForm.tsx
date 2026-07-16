import type { ClubSpecification } from "../api/types";
import { CLUB_TYPES } from "../api/types";
import { NumberField } from "./NumberField";

interface Props {
  value: ClubSpecification;
  onChange: (club: ClubSpecification) => void;
}

export function ClubSpecForm({ value, onChange }: Props) {
  function setField<K extends keyof ClubSpecification>(key: K, fieldValue: ClubSpecification[K]) {
    onChange({ ...value, [key]: fieldValue });
  }

  return (
    <div className="panel panel--spec">
      <h2>Club specification</h2>
      <div className="field-grid">
        <label className="field">
          <span>Club type</span>
          <select
            value={value.club_type}
            onChange={(event) => setField("club_type", event.target.value as ClubSpecification["club_type"])}
          >
            {CLUB_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>
        <NumberField label="Club length" unit="in" step={0.1} value={value.club_length} onChange={(v) => setField("club_length", v)} />
        <NumberField label="Loft" unit="deg" step={0.1} value={value.loft} onChange={(v) => setField("loft", v)} />
        <NumberField label="Lie angle" unit="deg" step={0.1} value={value.lie_angle} onChange={(v) => setField("lie_angle", v)} />
        <NumberField label="Head mass" unit="g" value={value.head_mass} onChange={(v) => setField("head_mass", v)} />
        <NumberField label="Shaft mass" unit="g" value={value.shaft_mass} onChange={(v) => setField("shaft_mass", v)} />
        <NumberField label="Shaft length" unit="in" step={0.1} value={value.shaft_length} onChange={(v) => setField("shaft_length", v)} />
        <NumberField label="Grip mass" unit="g" value={value.grip_mass} onChange={(v) => setField("grip_mass", v)} />
      </div>
    </div>
  );
}
