export function Loading({ text = "Loading…" }) {
  return (
    <div className="state">
      <span className="spinner" /> {text}
    </div>
  );
}

export function ErrorBox({ error, onRetry }) {
  return (
    <div className="state state-error">
      <strong>Couldn't reach the CareSlot API.</strong>
      <span>{error}</span>
      {onRetry && (
        <button className="btn btn-light" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function Empty({ text }) {
  return <div className="state muted">{text}</div>;
}
