export const PRIORITY_LABELS = {
  routine: "Routine",
  urgent: "Urgent",
};

export const STATUS_LABELS = {
  scheduled: "Scheduled",
  checked_in: "Checked in",
  completed: "Completed",
  cancelled: "Cancelled",
  no_show: "No show",
};

// the api returns UTC; postgres includes the offset, so Date() handles it.
// sqlite (local dev only) drops it, so treat a bare timestamp as UTC.
export function parseTime(value) {
  if (!value) return null;
  const hasZone = /([zZ]|[+-]\d\d:?\d\d)$/.test(value);
  return new Date(hasZone ? value : `${value}Z`);
}

export function formatTime(value) {
  return parseTime(value)?.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) ?? "";
}

export function formatDate(value) {
  return parseTime(value)?.toLocaleDateString([], { day: "numeric", month: "short" }) ?? "";
}

export function todayISO() {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function timeAgo(value) {
  const seconds = Math.max(0, (Date.now() - parseTime(value)) / 1000);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} h ago`;
  return formatDate(value);
}

export function initials(name = "") {
  return name
    .replace(/^Dr\.?\s+/i, "")
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0].toUpperCase())
    .join("");
}
