'use client';

import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { authApi, setTokens, clearTokens, getAccessToken, isAuthenticated as checkAuth } from '@/src/lib/api';
import type { LoginResponse, BorrowerResponse } from '@/src/types';

interface AuthContextType {
  user: BorrowerResponse | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: any) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<BorrowerResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const { data } = await authApi.getProfile();
      setUser(data);
    } catch {
      // If profile fetch fails, clear auth
      if (!getAccessToken()) {
        setUser(null);
      }
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      if (checkAuth()) {
        await refreshUser();
      }
      setLoading(false);
    };
    init();
  }, [refreshUser]);

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await authApi.login({ email, password });
    setTokens(data.access_token, data.refresh_token);
    await refreshUser();
  }, [refreshUser]);

  const register = useCallback(async (payload: any) => {
    const { data } = await authApi.register(payload);
    setTokens(data.access_token, data.refresh_token);
    await refreshUser();
  }, [refreshUser]);

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
