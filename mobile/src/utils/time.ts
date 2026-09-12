// Time / date formatting helpers. Purely presentational — the backend is the
// authority for all computed durations (current_work_minutes, total_work_minutes).

/** Formats a minute count as "Hh Mm" (e.g. 135 -> "2h 15m"). */
export function formatMinutes(minutes: number | null | undefined): string {
  if (minutes == null || minutes < 0 || Number.isNaN(minutes)) return '0h 00m';
  const total = Math.floor(minutes);
  const h = Math.floor(total / 60);
  const m = total % 60;
  return `${h}h ${String(m).padStart(2, '0')}m`;
}

/** Parses an ISO string to a Date, returning null on failure. */
export function parseIso(iso: string | null | undefined): Date | null {
  if (!iso) return null;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? null : d;
}

/** Formats an ISO timestamp as a local clock time (e.g. "09:04 AM"). */
export function formatClock(iso: string | null | undefined): string {
  const d = parseIso(iso);
  if (!d) return '--:--';
  return d.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  });
}

/** Formats an ISO date/timestamp as a readable date (e.g. "Sat, Sep 13, 2026"). */
export function formatDate(iso: string | null | undefined): string {
  const d = parseIso(iso);
  if (!d) return '--';
  return d.toLocaleDateString(undefined, {
    weekday: 'short',
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/** Short date form (e.g. "Sep 13, 2026") for lists. */
export function formatShortDate(iso: string | null | undefined): string {
  const d = parseIso(iso);
  if (!d) return '--';
  return d.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/** Returns a greeting based on the local hour of day. */
export function greeting(now: Date = new Date()): string {
  const h = now.getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
}
