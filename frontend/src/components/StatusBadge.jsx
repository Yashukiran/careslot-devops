import { STATUS_LABELS } from "../utils.js";

export default function StatusBadge({ status }) {
  return <span className={`badge badge-${status}`}>{STATUS_LABELS[status] ?? status}</span>;
}

export function PriorityBadge({ priority }) {
  if (priority !== "urgent") return null;
  return <span className="badge badge-urgent">Urgent</span>;
}
