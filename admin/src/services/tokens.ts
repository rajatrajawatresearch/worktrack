// Token storage in localStorage. Kept separate from api.ts to avoid a circular
// import (auth.ts uses api.ts, api.ts uses tokens.ts).
const ACCESS_KEY = 'wt_access_token';
const REFRESH_KEY = 'wt_refresh_token';

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens(access: string, refresh: string): void {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}
