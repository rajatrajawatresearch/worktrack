import AsyncStorage from '@react-native-async-storage/async-storage';

import type { TokenUser } from '../types';

const ACCESS_KEY = 'wt.access_token';
const REFRESH_KEY = 'wt.refresh_token';
const USER_KEY = 'wt.user';

export interface StoredSession {
  accessToken: string;
  refreshToken: string;
  user: TokenUser;
}

export async function saveSession(session: StoredSession): Promise<void> {
  await AsyncStorage.multiSet([
    [ACCESS_KEY, session.accessToken],
    [REFRESH_KEY, session.refreshToken],
    [USER_KEY, JSON.stringify(session.user)],
  ]);
}

export async function updateTokens(accessToken: string, refreshToken: string): Promise<void> {
  await AsyncStorage.multiSet([
    [ACCESS_KEY, accessToken],
    [REFRESH_KEY, refreshToken],
  ]);
}

export async function loadSession(): Promise<StoredSession | null> {
  const entries = await AsyncStorage.multiGet([ACCESS_KEY, REFRESH_KEY, USER_KEY]);
  const map = new Map(entries);
  const accessToken = map.get(ACCESS_KEY);
  const refreshToken = map.get(REFRESH_KEY);
  const userRaw = map.get(USER_KEY);
  if (!accessToken || !refreshToken || !userRaw) return null;
  try {
    const user = JSON.parse(userRaw) as TokenUser;
    return { accessToken, refreshToken, user };
  } catch {
    return null;
  }
}

export async function clearSession(): Promise<void> {
  await AsyncStorage.multiRemove([ACCESS_KEY, REFRESH_KEY, USER_KEY]);
}

export async function getAccessToken(): Promise<string | null> {
  return AsyncStorage.getItem(ACCESS_KEY);
}

export async function getRefreshToken(): Promise<string | null> {
  return AsyncStorage.getItem(REFRESH_KEY);
}
