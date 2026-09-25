export function LoadingState({ label = "Loading…" }) {
  return (
    <div className="state-block">
      <strong>{label}</strong>
      <span>Please wait a moment.</span>
    </div>
  );
}

export function ErrorState({ message = "Something went wrong." }) {
  return (
    <div className="state-block">
      <strong>Couldn't load this data</strong>
      <span>{message}</span>
    </div>
  );
}

export function EmptyState({ title = "Nothing here yet", message }) {
  return (
    <div className="state-block">
      <strong>{title}</strong>
      {message && <span>{message}</span>}
    </div>
  );
}
