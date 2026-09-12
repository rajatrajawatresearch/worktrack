// Approximate client-side distance ONLY for UX. The backend is the authority
// for whether an attendance action is within the allowed radius.

/** Rounds a metre value for display (e.g. 123.7 -> "124 m"). */
export function formatMeters(meters: number | null | undefined): string {
  if (meters == null || Number.isNaN(meters)) return '--';
  return `${Math.round(meters)} m`;
}

const EARTH_RADIUS_M = 6371000;

function toRad(deg: number): number {
  return (deg * Math.PI) / 180;
}

/**
 * Haversine distance in metres between two coordinates. Approximate; used only
 * for optimistic UX before the server responds.
 */
export function haversineMeters(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number,
): number {
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return EARTH_RADIUS_M * c;
}
