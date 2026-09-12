// Authentication helpers: login/logout/refresh and current-user fetch.
import type { MeResponse, TokenResponse } from '../types';
import { post, get } from './api';
import * as tokens from './tokens';

export async function login(email: string, password: string): Promise<TokenResponse> {
  // Login is a public endpoint; do not attempt a 401 refresh/retry on it.
  const res = await post<TokenResponse>('/auth/login', { email, password });
  tokens.setTokens(res.access_token, res.refresh_token);
  return res;
}

export async function logout(): Promise<void> {
  const refresh = tokens.getRefreshToken();
  if (refresh) {
    try {
      await post<{ revoked: boolean }>('/auth/logout', { refresh_token: refresh });
    } catch {
      // Best-effort: even if revocation fails, we clear local tokens below.
    }
  }
  tokens.clearTokens();
}

export function getCurrentUser(): Promise<MeResponse> {
  return get<MeResponse>('/me');
}

export function isAuthenticated(): boolean {
  return tokens.getAccessToken() !== null;
}

export { getAccessToken, getRefreshToken, clearTokens, setTokens } from './tokens';
