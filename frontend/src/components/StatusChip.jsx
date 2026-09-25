const STATUS_TONE = {
  Draft: "neutral",
  Submitted: "info",
  "Under Review": "info",
  "Clarification Required": "warning",
  Validated: "primary",
  Approved: "success",
  Rejected: "danger",

  Portfolio: "neutral",
  Planned: "info",
  "In Progress": "primary",
  "At Risk": "warning",
  Blocked: "danger",
  Completed: "success",

  "On Track": "success",
  Overdue: "danger",

  Low: "neutral",
  Medium: "info",
  High: "danger",
};

export default function StatusChip({ value }) {
  if (!value) return null;
  const tone = STATUS_TONE[value] || "neutral";
  return <span className={`chip chip-${tone}`}>{value}</span>;
}
