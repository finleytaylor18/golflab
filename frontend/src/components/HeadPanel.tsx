import type { ClubSpecification } from "../api/types";
import { NumberField } from "./NumberField";

interface Props {
  value: ClubSpecification;
  onChange: (club: ClubSpecification) => void;
}

export function HeadPanel({ value, onChange }: Props) {
  return (
    <div className="panel panel--head">
      <h2>Head</h2>
      <NumberField
        label="Head mass"
        unit="g"
        value={value.head_mass}
        onChange={(head_mass) => onChange({ ...value, head_mass })}
      />
    </div>
  );
}
