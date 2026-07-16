import type { SwingProfile } from "../api/types";
import { NumberField } from "./NumberField";

interface Props {
  value: SwingProfile;
  onChange: (swing: SwingProfile) => void;
}

export function SwingProfileForm({ value, onChange }: Props) {
  function setField(key: keyof SwingProfile, fieldValue: number) {
    onChange({ ...value, [key]: fieldValue });
  }

  return (
    <div className="panel panel--swing">
      <h2>Swing profile</h2>
      <div className="field-grid">
        <NumberField label="Clubhead speed" unit="mph" value={value.clubhead_speed} onChange={(v) => setField("clubhead_speed", v)} />
        <NumberField label="Attack angle" unit="deg" step={0.5} value={value.attack_angle} onChange={(v) => setField("attack_angle", v)} />
        <NumberField label="Swing path" unit="deg" step={0.5} value={value.swing_path} onChange={(v) => setField("swing_path", v)} />
        <NumberField label="Face angle" unit="deg" step={0.5} value={value.face_angle} onChange={(v) => setField("face_angle", v)} />
        <NumberField label="Dynamic loft" unit="deg" step={0.5} value={value.dynamic_loft} onChange={(v) => setField("dynamic_loft", v)} />
      </div>
    </div>
  );
}
