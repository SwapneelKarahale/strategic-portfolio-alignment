export default function PageHeader({ title, actions }) {
  return (
    <div className="topbar">
      <h1>{title}</h1>
      <div style={{ display: "flex", gap: 8 }}>{actions}</div>
    </div>
  );
}
