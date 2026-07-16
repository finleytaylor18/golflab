import type { ClubSpecification } from "../api/types";
import { CLUB_TYPES } from "../api/types";
import { NumberField } from "./NumberField";

interface Props {
  value: ClubSpecification;
  onChange: (club: ClubSpecification) => void;
}

export function SpecPanel({ value, onChange }: Props) {
  return (
    <div className="panel panel--spec">
      <h2>Overall spec</h2>
      <label className="field">
        <span>Club type</span>
        <select
          value={value.club_type}
          onChange={(event) => onChange({ ...value, club_type: event.target.value as ClubSpecification["club_type"] })}
        >
          {CLUB_TYPES.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </label>
      <NumberField
        label="Club length"
        unit="in"
        step={0.1}
        value={value.club_length}
        onChange={(club_length) => onChange({ ...value, club_length })}
      />
      <NumberField label="Loft" unit="deg" step={0.1} value={value.loft} onChange={(loft) => onChange({ ...value, loft })} />
      <NumberField
        label="Lie angle"
        unit="deg"
        step={0.1}
        value={value.lie_angle}
        onChange={(lie_angle) => onChange({ ...value, lie_angle })}
      />
    </div>
  );
}
