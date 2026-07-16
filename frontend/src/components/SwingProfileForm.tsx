import type { SwingProfile } from "../api/types";

interface Props {
  value: SwingProfile;
  onChange: (swing: SwingProfile) => void;
}

interface FieldDef {
  key: keyof SwingProfile;
  label: string;
  unit: string;
  step: number;
}

const FIELDS: FieldDef[] = [
  { key: "clubhead_speed", label: "Clubhead speed", unit: "mph", step: 1 },
  { key: "attack_angle", label: "Attack angle", unit: "deg", step: 0.5 },
  { key: "swing_path", label: "Swing path", unit: "deg", step: 0.5 },
  { key: "face_angle", label: "Face angle", unit: "deg", step: 0.5 },
  { key: "dynamic_loft", label: "Dynamic loft", unit: "deg", step: 0.5 },
];

export function SwingProfileForm({ value, onChange }: Props) {
  function setField(key: keyof SwingProfile, fieldValue: number) {
    onChange({ ...value, [key]: fieldValue });
  }

  return (
    <div className="panel">
      <h2>Swing profile</h2>
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
