import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from "recharts";

interface Props {
  points: [number, number, number][];
}

export function TrajectoryCharts({ points }: Props) {
  const data = points.map(([distance, lateral, height]) => ({ distance, lateral, height }));
  const maxLateral = Math.max(10, ...data.map((p) => Math.abs(p.lateral)));

  return (
    <div className="charts">
      <div className="chart">
        <h3>Top-down (shot shape)</h3>
        <ResponsiveContainer width="100%" height={160}>
          <LineChart data={data} margin={{ top: 5, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="distance" tick={{ fontSize: 11 }} unit="yd" stroke="var(--text-muted)" />
            <YAxis dataKey="lateral" domain={[-maxLateral * 1.2, maxLateral * 1.2]} tick={{ fontSize: 11 }} unit="yd" stroke="var(--text-muted)" />
            <ReferenceLine y={0} stroke="var(--border)" />
            <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", fontSize: 12 }} />
            <Line type="monotone" dataKey="lateral" stroke="var(--accent)" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="chart">
        <h3>Side view (trajectory)</h3>
        <ResponsiveContainer width="100%" height={160}>
          <LineChart data={data} margin={{ top: 5, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="distance" tick={{ fontSize: 11 }} unit="yd" stroke="var(--text-muted)" />
            <YAxis dataKey="height" tick={{ fontSize: 11 }} unit="yd" stroke="var(--text-muted)" />
            <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", fontSize: 12 }} />
            <Line type="monotone" dataKey="height" stroke="var(--accent)" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
