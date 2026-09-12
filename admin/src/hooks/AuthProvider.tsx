import { useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import type { Company, TokenUser, User } from '../types';
import * as auth from '../services/auth';
import { setSessionExpiredHandler } from '../services/api';
import { AuthContext } from './AuthContext';
import type { AuthState } from './AuthContext';

const SELECTED_COMPANY_KEY = 'wt_selected_company_id';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | TokenUser | null>(null);
  const [company, setCompany] = useState<Company | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedCompanyId, setSelectedCompanyIdState] = useState<string | null>(
    () => localStorage.getItem(SELECTED_COMPANY_KEY),
  );

  const setSelectedCompanyId = useCallback((id: string | null) => {
    setSelectedCompanyIdState(id);
    if (id) localStorage.setItem(SELECTED_COMPANY_KEY, id);
    else localStorage.removeItem(SELECTED_COMPANY_KEY);
  }, []);

  const clearSession = useCallback(() => {
    setUser(null);
    setCompany(null);
    setSelectedCompanyId(null);
  }, [setSelectedCompanyId]);

  const refreshMe = useCallback(async () => {
    const me = await auth.getCurrentUser();
    setUser(me.user);
    setCompany(me.company);
  }, []);

  // Wire the api layer's "session expired" callback to clear local state.
  useEffect(() => {
    setSessionExpiredHandler(() => {
      clearSession();
    });
  }, [clearSession]);

  // Bootstrap: if we have a token, resolve the current user.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!auth.isAuthenticated()) {
        setLoading(false);
        return;
      }
      try {
        const me = await auth.getCurrentUser();
        if (!cancelled) {
          setUser(me.user);
          setCompany(me.company);
        }
      } catch {
        if (!cancelled) clearSession();
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [clearSession]);

  const doLogin = useCallback(async (email: string, password: string) => {
    const res = await auth.login(email, password);
    setUser(res.user);
    // Resolve full profile (including company) after login.
    try {
      const me = await auth.getCurrentUser();
      setUser(me.user);
      setCompany(me.company);
    } catch {
      // Fall back to the token user if /me fails for any reason.
    }
  }, []);

  const doLogout = useCallback(async () => {
    await auth.logout();
    clearSession();
  }, [clearSession]);

  const value = useMemo<AuthState>(
    () => ({
      user,
      company,
      role: user?.role ?? null,
      loading,
      selectedCompanyId,
      setSelectedCompanyId,
      login: doLogin,
      logout: doLogout,
      refreshMe,
    }),
    [user, company, loading, selectedCompanyId, setSelectedCompanyId, doLogin, doLogout, refreshMe],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
