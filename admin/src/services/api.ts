// Lightweight fetch wrapper around the WorkTrack API.
// - prefixes the base url
// - attaches the bearer access token
// - unwraps the { success, data, pagination } envelope
// - on 401 tries a single refresh + retry, otherwise clears the session
import type { ApiEnvelope, Pagination } from '../types';
import * as tokens from './tokens';

export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/+$/, '') ??
  'http://localhost:8000/api/v1';

export class ApiError extends Error {
  code: string;
  status: number;
  details?: Record<string, unknown>;

  constructor(code: string, message: string, status: number, details?: Record<string, unknown>) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

export interface ListResult<T> {
  data: T[];
  pagination: Pagination;
}

type QueryValue = string | number | boolean | null | undefined;
export type Query = Record<string, QueryValue>;

function buildUrl(path: string, query?: Query): string {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

// Callback invoked when the session can no longer be recovered (refresh failed).
let onSessionExpired: (() => void) | null = null;
export function setSessionExpiredHandler(handler: () => void): void {
  onSessionExpired = handler;
}

let refreshInFlight: Promise<boolean> | null = null;

async function tryRefresh(): Promise<boolean> {
  const refreshToken = tokens.getRefreshToken();
  if (!refreshToken) return false;

  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const res = await fetch(buildUrl('/auth/refresh'), {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
        const json = (await res.json().catch(() => null)) as ApiEnvelope<{
          access_token: string;
          refresh_token: string;
          token_type: string;
        }> | null;
        if (!res.ok || !json || json.success !== true) {
          return false;
        }
        tokens.setTokens(json.data.access_token, json.data.refresh_token);
        return true;
      } catch {
        return false;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  query?: Query;
  retryOn401?: boolean;
}

async function rawRequest(path: string, opts: RequestOptions): Promise<Response> {
  const headers: Record<string, string> = {};
  const access = tokens.getAccessToken();
  if (access) headers['Authorization'] = `Bearer ${access}`;

  let body: BodyInit | undefined;
  if (opts.body !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(opts.body);
  }

  return fetch(buildUrl(path, opts.query), {
    method: opts.method ?? 'GET',
    headers,
    body,
  });
}

async function parseEnvelope<T>(res: Response): Promise<ApiEnvelope<T>> {
  const text = await res.text();
  if (!text) {
    if (res.ok) {
      return { success: true, data: undefined as unknown as T };
    }
    throw new ApiError('INTERNAL_ERROR', `Request failed (${res.status})`, res.status);
  }
  try {
    return JSON.parse(text) as ApiEnvelope<T>;
  } catch {
    throw new ApiError('INTERNAL_ERROR', `Unexpected response (${res.status})`, res.status);
  }
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<ApiEnvelope<T>> {
  const retryOn401 = opts.retryOn401 ?? true;
  let res = await rawRequest(path, opts);

  if (res.status === 401 && retryOn401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      res = await rawRequest(path, opts);
    } else {
      tokens.clearTokens();
      if (onSessionExpired) onSessionExpired();
      throw new ApiError('NOT_AUTHENTICATED', 'Your session has expired. Please sign in again.', 401);
    }
  }

  const json = await parseEnvelope<T>(res);
  if (json.success === false) {
    throw new ApiError(json.error.code, json.error.message, res.status, json.error.details);
  }
  if (!res.ok) {
    throw new ApiError('INTERNAL_ERROR', `Request failed (${res.status})`, res.status);
  }
  return json;
}

export async function get<T>(path: string, query?: Query): Promise<T> {
  const json = (await request<T>(path, { method: 'GET', query })) as { data: T };
  return json.data;
}

export async function getList<T>(path: string, query?: Query): Promise<ListResult<T>> {
  const json = await request<T[]>(path, { method: 'GET', query });
  const pagination: Pagination =
    'pagination' in json && json.pagination
      ? json.pagination
      : { page: 1, page_size: (json.data as T[]).length, total: (json.data as T[]).length, total_pages: 1 };
  return { data: json.data as T[], pagination };
}

export async function post<T>(path: string, body?: unknown, query?: Query): Promise<T> {
  const json = (await request<T>(path, { method: 'POST', body, query })) as { data: T };
  return json.data;
}

export async function patch<T>(path: string, body?: unknown, query?: Query): Promise<T> {
  const json = (await request<T>(path, { method: 'PATCH', body, query })) as { data: T };
  return json.data;
}

// Downloads a blob (e.g. CSV export) and triggers a browser save.
// Refreshes the access token on 401 exactly once.
export async function downloadBlob(path: string, query: Query, filename: string): Promise<void> {
  let res = await rawRequest(path, { method: 'GET', query });
  if (res.status === 401) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      res = await rawRequest(path, { method: 'GET', query });
    } else {
      tokens.clearTokens();
      if (onSessionExpired) onSessionExpired();
      throw new ApiError('NOT_AUTHENTICATED', 'Your session has expired. Please sign in again.', 401);
    }
  }
  if (!res.ok) {
    // Attempt to surface a structured error message.
    const json = (await res.json().catch(() => null)) as ApiEnvelope<unknown> | null;
    if (json && json.success === false) {
      throw new ApiError(json.error.code, json.error.message, res.status, json.error.details);
    }
    throw new ApiError('INTERNAL_ERROR', `Download failed (${res.status})`, res.status);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
