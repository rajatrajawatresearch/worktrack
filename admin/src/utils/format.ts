// Presentation helpers shared across pages.

// "8h 30m" style formatting from a minute count.
export function formatMinutes(minutes: number | null | undefined): string {
  if (minutes === null || minutes === undefined) return '—';
  if (minutes <= 0) return '0m';
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  if (h === 0) return `${m}m`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

// ISO timestamp -> local time (e.g. "9:04 AM").
export function formatTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
}

// ISO timestamp -> local date + time.
export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

// Date-only string (YYYY-MM-DD) -> "Sep 13, 2026".
export function formatDate(value: string | null | undefined): string {
  if (!value) return '—';
  // Treat plain YYYY-MM-DD as a local calendar date (avoid TZ shifting).
  const d = /^\d{4}-\d{2}-\d{2}$/.test(value) ? new Date(`${value}T00:00:00`) : new Date(value);
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
}

// Today's date as YYYY-MM-DD in local time.
export function todayIso(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

// Human label for an attendance status enum value.
export function statusLabel(status: string): string {
  return status
    .split('_')
    .map((w) => w.charAt(0) + w.slice(1).toLowerCase())
    .join(' ');
}

// CSS modifier class for a status badge.
export function statusClass(status: string): string {
  switch (status) {
    case 'IN_PROGRESS':
      return 'badge--info';
    case 'ON_BREAK':
      return 'badge--warn';
    case 'COMPLETED':
    case 'PRESENT':
      return 'badge--ok';
    case 'ABSENT':
    case 'MISSED_PUNCH':
      return 'badge--danger';
    default:
      return 'badge--muted';
  }
}
