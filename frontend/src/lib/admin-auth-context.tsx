'use client';

import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { adminAuthApi, setAdminTokens, clearAdminTokens, getAdminAccessToken, isAdminAuthenticated as checkAdminAuth } from '@/src/lib/admin-api';

interface AdminUser {
  admin_id: string;
  email: string;
  name: string;
  role: string;
}

interface AdminAuthContextType {
  user: AdminUser | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string, mfa_code?: string) => Promise<void>;
  logout: () => void;
}

const AdminAuthContext = createContext<AdminAuthContextType | undefined>(undefined);

export function AdminAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AdminUser | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchProfile = useCallback(async () => {
    try {
      const { data } = await adminAuthApi.getProfile();
      setUser({
        admin_id: data.admin_id || data.id,
        email: data.email,
        name: data.name || `${data.first_name || ''} ${data.last_name || ''}`.trim(),
        role: data.role || 'admin',
      });
    } catch {
      if (!getAdminAccessToken()) {
        setUser(null);
      }
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      if (checkAdminAuth()) {
        await fetchProfile();
      }
      setLoading(false);
    };
    init();
  }, [fetchProfile]);

  const login = useCallback(async (email: string, password: string, mfa_code?: string) => {
    const { data } = await adminAuthApi.login({ email, password, mfa_code });
    setAdminTokens(data.access_token, data.refresh_token);
    setUser({
      admin_id: data.admin_id,
      email: data.email,
      name: data.name,
      role: data.role,
    });
  }, []);

  const logout = useCallback(() => {
    clearAdminTokens();
    setUser(null);
    if (typeof window !== 'undefined') {
      window.location.href = '/admin/login';
    }
  }, []);

  return (
    <AdminAuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        logout,
      }}
    >
      {children}
    </AdminAuthContext.Provider>
  );
}

export function useAdminAuth() {
  const context = useContext(AdminAuthContext);
  if (context === undefined) {
    throw new Error('useAdminAuth must be used within an AdminAuthProvider');
  }
  return context;
}
