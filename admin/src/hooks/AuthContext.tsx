import { createContext } from 'react';
import type { Company, TokenUser, User } from '../types';

export interface AuthState {
  user: User | TokenUser | null;
  company: Company | null;
  role: string | null;
  loading: boolean;
  // SUPER_ADMIN active company selection (drives ?company_id=). null = all companies.
  selectedCompanyId: string | null;
  setSelectedCompanyId: (id: string | null) => void;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshMe: () => Promise<void>;
}

export const AuthContext = createContext<AuthState | null>(null);
