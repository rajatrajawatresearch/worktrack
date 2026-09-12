import * as Location from 'expo-location';

import type { LocationPayload } from '../types';

export type PermissionState = 'granted' | 'denied' | 'undetermined';

export interface LocationFixResult {
  ok: boolean;
  /** Present when ok === true. */
  payload?: LocationPayload;
  /** Present when ok === false: a client-side reason for UX. */
  reason?: 'PERMISSION_DENIED' | 'LOCATION_UNAVAILABLE';
  message?: string;
}

export async function getPermissionStatus(): Promise<PermissionState> {
  const { status } = await Location.getForegroundPermissionsAsync();
  return normalize(status);
}

export async function requestPermission(): Promise<PermissionState> {
  const { status } = await Location.requestForegroundPermissionsAsync();
  return normalize(status);
}

function normalize(status: Location.PermissionStatus): PermissionState {
  if (status === Location.PermissionStatus.GRANTED) return 'granted';
  if (status === Location.PermissionStatus.DENIED) return 'denied';
  return 'undetermined';
}

/**
 * Requests foreground permission (explaining why is the caller's job) and
 * returns a single high-accuracy GPS fix. Never runs background location.
 */
export async function getCurrentFix(): Promise<LocationFixResult> {
  let permission = await getPermissionStatus();
  if (permission !== 'granted') {
    permission = await requestPermission();
  }
  if (permission !== 'granted') {
    return {
      ok: false,
      reason: 'PERMISSION_DENIED',
      message: 'Location permission is required to record attendance.',
    };
  }

  try {
    const enabled = await Location.hasServicesEnabledAsync();
    if (!enabled) {
      return {
        ok: false,
        reason: 'LOCATION_UNAVAILABLE',
        message: 'Location services are turned off. Please enable them and try again.',
      };
    }
    const fix = await Location.getCurrentPositionAsync({
      accuracy: Location.Accuracy.High,
    });
    return {
      ok: true,
      payload: {
        latitude: fix.coords.latitude,
        longitude: fix.coords.longitude,
        // accuracy can be null on some devices; fall back to a large value so
        // the server applies its GPS_ACCURACY_TOO_LOW policy.
        accuracy: fix.coords.accuracy ?? 9999,
        client_timestamp: new Date(fix.timestamp).toISOString(),
      },
    };
  } catch {
    return {
      ok: false,
      reason: 'LOCATION_UNAVAILABLE',
      message: 'Could not get your location. Please try again.',
    };
  }
}
