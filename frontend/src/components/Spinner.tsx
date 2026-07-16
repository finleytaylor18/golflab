interface Props {
  label: string;
}

export function Spinner({ label }: Props) {
  return (
    <div className="spinner-container">
      <div className="spinner" aria-hidden="true" />
      <span>{label}</span>
    </div>
  );
}
