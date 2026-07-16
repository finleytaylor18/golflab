interface Props {
  loading: boolean;
  error: string | null;
  swingWeight: string | null;
  moment: number | null;
  moi: number | null;
  balancePoint: number | null;
}

export function ResultsDisplay({ loading, error, swingWeight, moment, moi, balancePoint }: Props) {
  return (
    <div className="panel panel--results">
      <h2>Computed metrics</h2>
      {error && <p className="error">{error}</p>}
      {!error && (
        <dl className="results">
          <dt>Swing weight</dt>
          <dd>
            {swingWeight ?? "—"}
            {moment !== null && ` (${moment.toFixed(2)} gram-inches)`}
          </dd>
          <dt>MOI</dt>
          <dd>{moi !== null ? `${moi.toFixed(2)} gram-inches²` : "—"}</dd>
          <dt>Balance point</dt>
          <dd>{balancePoint !== null ? `${balancePoint.toFixed(2)} in from butt` : "—"}</dd>
        </dl>
      )}
      {loading && <p className="status">Recalculating…</p>}
    </div>
  );
}
