import type { ClubSpecification } from "../api/types";
import { CLUB_TYPES } from "../api/types";

interface Props {
  value: ClubSpecification;
  onChange: (club: ClubSpecification) => void;
}

interface FieldDef {
  key: keyof Omit<ClubSpecification, "club_type">;
  label: string;
  unit: string;
  step: number;
}

const FIELDS: FieldDef[] = [
  { key: "head_mass", label: "Head mass", unit: "g", step: 1 },
  { key: "shaft_mass", label: "Shaft mass", unit: "g", step: 1 },
  { key: "shaft_length", label: "Shaft length", unit: "in", step: 0.1 },
  { key: "grip_mass", label: "Grip mass", unit: "g", step: 1 },
  { key: "club_length", label: "Club length", unit: "in", step: 0.1 },
  { key: "loft", label: "Loft", unit: "deg", step: 0.1 },
  { key: "lie_angle", label: "Lie angle", unit: "deg", step: 0.1 },
];

export function ClubSpecForm({ value, onChange }: Props) {
  function setField<K extends keyof ClubSpecification>(key: K, fieldValue: ClubSpecification[K]) {
    onChange({ ...value, [key]: fieldValue });
  }

  return (
    <div className="panel">
      <h2>Club specification</h2>

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

      {FIELDS.map(({ key, label, unit, step }) => (
        <label className="field" key={key}>
          <span>
            {label} <em>({unit})</em>
          </span>
          <input
            type="number"
            step={step}
            value={value[key]}
            onChange={(event) => setField(key, Number(event.target.value))}
          />
        </label>
      ))}
    </div>
  );
}
