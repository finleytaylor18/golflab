import type { ClubSpecification } from "../api/types";
import { NumberField } from "./NumberField";

interface Props {
  value: ClubSpecification;
  onChange: (club: ClubSpecification) => void;
}

export function GripPanel({ value, onChange }: Props) {
  return (
    <div className="panel panel--grip">
      <h2>Grip</h2>
      <NumberField
        label="Grip mass"
        unit="g"
        value={value.grip_mass}
        onChange={(grip_mass) => onChange({ ...value, grip_mass })}
      />
    </div>
  );
}
