import type {
  ApiErrorPayload,
  ErrorEnvelope,
  PaginationMeta,
  SuccessEnvelope,
  TokenPairResponse,
} from '../types';
import * as storage from './storage';

export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:8000/api/v1';

/** Error thrown for any non-success outcome so callers can branch on `code`. */
export class ApiError extends Error {
  code: string;
  status: number;
  details?: Record<string, unknown>;

  constructor(payload: ApiErrorPayload, status: number) {
    super(payload.message);
    this.name = 'ApiError';
    this.code = payload.code;
    this.status = status;
    this.details = payload.details;
  }
}

// Client-only codes (never returned by the server) for transport failures.
export const CLIENT_NETWORK_ERROR = 'NETWORK_ERROR';
export const CLIENT_BAD_RESPONSE = 'BAD_RESPONSE';

export interface RequestResult<T> {
  data: T;
  pagination?: PaginationMeta;
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  body?: unknown;
  /** Set false for auth endpoints that must not carry / refresh a bearer token. */
  auth?: boolean;
  query?: Record<string, string | number | undefined | null>;
  /** Internal: prevents infinite refresh loops. */
  _retried?: boolean;
}

// Callback invoked when refresh fails and the session must be discarded.
let onSessionExpired: (() => void) | null = null;
export function setSessionExpiredHandler(handler: (() => void) | null): void {
  onSessionExpired = handler;
}

// Guards concurrent refreshes so only one runs at a time.
let refreshPromise: Promise<boolean> | null = null;

function buildUrl(path: string, query?: RequestOptions['query']): string {
  const base = API_BASE_URL.replace(/\/$/, '');
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  const url = `${base}${cleanPath}`;
  if (!query) return url;
  const params = Object.entries(query)
    .filter(([, v]) => v !== undefined && v !== null && v !== '')
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`);
  return params.length ? `${url}?${params.join('&')}` : url;
}

async function attemptRefresh(): Promise<boolean> {
  if (refreshPromise) return refreshPromise;
  refreshPromise = (async () => {
    const refreshToken = await storage.getRefreshToken();
    if (!refreshToken) return false;
    try {
      const res = await fetch(buildUrl('/auth/refresh'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      const json = (await res.json()) as
        | SuccessEnvelope<TokenPairResponse>
        | ErrorEnvelope;
      if (!res.ok || !json.success) return false;
      await storage.updateTokens(json.data.access_token, json.data.refresh_token);
      return true;
    } catch {
      return false;
    }
  })();
  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

export async function request<T>(
  path: string,
  options: RequestOptions = {},
): Promise<RequestResult<T>> {
  const { method = 'GET', body, auth = true, query, _retried = false } = options;

  const headers: Record<string, string> = {
    Accept: 'application/json',
  };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth) {
    const token = await storage.getAccessToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  let res: Response;
  try {
    res = await fetch(buildUrl(path, query), {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    // fetch rejects on connectivity failures / DNS / timeouts.
    throw new ApiError(
      {
        code: CLIENT_NETWORK_ERROR,
        message: 'Internet connection required to record attendance.',
      },
      0,
    );
  }

  // Attempt token refresh once on 401 for authenticated requests.
  if (res.status === 401 && auth && !_retried) {
    const refreshed = await attemptRefresh();
    if (refreshed) {
      return request<T>(path, { ...options, _retried: true });
    }
    await storage.clearSession();
    if (onSessionExpired) onSessionExpired();
  }

  let json: SuccessEnvelope<T> | ErrorEnvelope;
  try {
    json = (await res.json()) as SuccessEnvelope<T> | ErrorEnvelope;
  } catch {
    throw new ApiError(
      {
        code: CLIENT_BAD_RESPONSE,
        message: 'The server returned an unexpected response.',
      },
      res.status,
    );
  }

  if (!json || typeof json !== 'object' || !('success' in json)) {
    throw new ApiError(
      {
        code: CLIENT_BAD_RESPONSE,
        message: 'The server returned an unexpected response.',
      },
      res.status,
    );
  }

  if (json.success) {
    return { data: json.data, pagination: json.pagination };
  }

  throw new ApiError(json.error, res.status);
}
