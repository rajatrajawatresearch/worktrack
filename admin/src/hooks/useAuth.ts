import { useContext } from 'react';
import { AuthContext } from './AuthContext';
import type { AuthState } from './AuthContext';

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}

// Convenience: the effective company_id a SUPER_ADMIN has selected, or the
// COMPANY_ADMIN's own company. Returns undefined when nothing is scoped.
export function useEffectiveCompanyId(): string | undefined {
  const { role, company, selectedCompanyId } = useAuth();
  if (role === 'SUPER_ADMIN') {
    return selectedCompanyId ?? undefined;
  }
  return company?.id ?? undefined;
}
