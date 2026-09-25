export default function KpiCard({ label, value, tone = "primary" }) {
  return (
    <div className="card kpi-card">
      <span className="kpi-label">{label}</span>
      <span className="kpi-value" style={{ color: `var(--color-${tone})` }}>
        {value}
      </span>
    </div>
  );
}
