import type { ClubSpecification } from "../api/types";
import { NumberField } from "./NumberField";

interface Props {
  value: ClubSpecification;
  onChange: (club: ClubSpecification) => void;
}

export function ShaftPanel({ value, onChange }: Props) {
  return (
    <div className="panel panel--shaft">
      <h2>Shaft</h2>
      <NumberField
        label="Shaft mass"
        unit="g"
        value={value.shaft_mass}
        onChange={(shaft_mass) => onChange({ ...value, shaft_mass })}
      />
      <NumberField
        label="Shaft length"
        unit="in"
        step={0.1}
        value={value.shaft_length}
        onChange={(shaft_length) => onChange({ ...value, shaft_length })}
      />
    </div>
  );
}
