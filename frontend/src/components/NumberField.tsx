interface Props {
  label: string;
  unit: string;
  value: number;
  step?: number;
  onChange: (value: number) => void;
}

export function NumberField({ label, unit, value, step = 1, onChange }: Props) {
  return (
    <label className="field">
      <span>
        {label} <em>({unit})</em>
      </span>
      <input type="number" step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} />
    </label>
  );
}
