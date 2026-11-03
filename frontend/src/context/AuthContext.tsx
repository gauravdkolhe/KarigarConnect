import React, { createContext, useContext, useEffect, useState } from 'react';
import type { UserProfile } from '../types';
import { api } from '../services/api';

interface AuthContextType {
  user: UserProfile | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, pass: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => void;
  updateProfile: (data: any) => Promise<UserProfile>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(() => {
    try {
      const saved = localStorage.getItem('karigar_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      localStorage.removeItem('karigar_user');
      return null;
    }
  });
  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('karigar_token');
  });
  // Only loading if there is actually a token to verify
  const [isLoading, setIsLoading] = useState<boolean>(() => {
    return !!localStorage.getItem('karigar_token');
  });

  useEffect(() => {
    let cancelled = false;

    async function loadUser() {
      if (token) {
        try {
          const timeoutPromise = new Promise<never>((_, reject) =>
            setTimeout(() => reject(new Error('Auth verification timeout')), 3000)
          );
          const profile = await Promise.race([api.getMe(), timeoutPromise]);
          if (!cancelled) {
            setUser(profile);
            localStorage.setItem('karigar_user', JSON.stringify(profile));
          }
        } catch {
          if (!cancelled) {
            logout();
          }
        }
      }
      if (!cancelled) {
        setIsLoading(false);
      }
    }
    loadUser();

    return () => {
      cancelled = true;
    };
  }, [token]);

  const login = async (email: string, pass: string) => {
    const res = await api.login(email, pass);
    setUser(res.user);
    setToken(res.access_token);
  };

  const register = async (data: any) => {
    await api.register(data);
    await login(data.email, data.password);
  };

  const logout = () => {
    api.logout();
    setUser(null);
    setToken(null);
  };

  const updateProfile = async (data: any) => {
    const updated = await api.updateMe(data);
    setUser(updated);
    return updated;
  };

  const refreshUser = async () => {
    if (token) {
      const profile = await api.getMe();
      setUser(profile);
      localStorage.setItem('karigar_user', JSON.stringify(profile));
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAuthenticated: !!token && !!user,
        login,
        register,
        logout,
        updateProfile,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
