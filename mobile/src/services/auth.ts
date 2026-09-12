import type {
  LocationPayload,
  MeResponse,
  PunchResult,
  TodayState,
  TokenResponse,
  AttendanceOut,
} from '../types';
import { request, type RequestResult } from './api';
import * as storage from './storage';

// ---- Auth ----
export async function login(email: string, password: string): Promise<TokenResponse> {
  const { data } = await request<TokenResponse>('/auth/login', {
    method: 'POST',
    auth: false,
    body: { email, password },
  });
  await storage.saveSession({
    accessToken: data.access_token,
    refreshToken: data.refresh_token,
    user: data.user,
  });
  return data;
}

export async function logout(): Promise<void> {
  const refreshToken = await storage.getRefreshToken();
  // Best-effort server-side revoke; always clear local session regardless.
  if (refreshToken) {
    try {
      await request<{ revoked: boolean }>('/auth/logout', {
        method: 'POST',
        body: { refresh_token: refreshToken },
      });
    } catch {
      // ignore network / auth failures on logout
    }
  }
  await storage.clearSession();
}

export async function fetchMe(): Promise<MeResponse> {
  const { data } = await request<MeResponse>('/me');
  return data;
}

// ---- Attendance ----
export async function fetchToday(): Promise<TodayState> {
  const { data } = await request<TodayState>('/attendance/today');
  return data;
}

type PunchEndpoint =
  | '/attendance/punch-in'
  | '/attendance/break/start'
  | '/attendance/break/end'
  | '/attendance/punch-out';

async function punchAction(
  endpoint: PunchEndpoint,
  payload: LocationPayload,
): Promise<PunchResult> {
  const { data } = await request<PunchResult>(endpoint, {
    method: 'POST',
    body: payload,
  });
  return data;
}

export const punchIn = (payload: LocationPayload) =>
  punchAction('/attendance/punch-in', payload);
export const startBreak = (payload: LocationPayload) =>
  punchAction('/attendance/break/start', payload);
export const endBreak = (payload: LocationPayload) =>
  punchAction('/attendance/break/end', payload);
export const punchOut = (payload: LocationPayload) =>
  punchAction('/attendance/punch-out', payload);

export interface HistoryQuery {
  page?: number;
  pageSize?: number;
  from?: string; // YYYY-MM-DD
  to?: string; // YYYY-MM-DD
}

export async function fetchHistory(
  q: HistoryQuery = {},
): Promise<RequestResult<AttendanceOut[]>> {
  return request<AttendanceOut[]>('/attendance/history', {
    query: {
      page: q.page,
      page_size: q.pageSize,
      from: q.from,
      to: q.to,
    },
  });
}
