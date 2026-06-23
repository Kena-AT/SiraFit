'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useNavigate } from '@tanstack/react-router';

type User = {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  is_verified: boolean;
};

type AuthContextType = {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (email: string, password: string, full_name?: string) => Promise<void>;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Check for existing session on mount
  useEffect(() => {
    const checkSession = async () => {
      try {
        const response = await fetch(`${API_URL}/api/v1/users/me`, { credentials: 'include' });
        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
        }
      } catch (error) {
        console.error('Failed to check session:', error);
      } finally {
        setIsLoading(false);
      }
    };
    checkSession();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username: email, password }),
      credentials: 'include',
    });

    if (response.ok) {
      // Cookies are automatically set by backend.
      // Now fetch user details.
      const meResponse = await fetch(`${API_URL}/api/v1/users/me`, { credentials: 'include' });
      if (meResponse.ok) {
        const userData = await meResponse.json();
        setUser(userData);
        navigate({ to: '/dashboard' });
      } else {
        throw new Error('Failed to fetch user details after login');
      }
    } else {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Login failed');
    }
  };

  const logout = async () => {
    try {
      await fetch(`${API_URL}/api/v1/auth/logout`, {
        method: 'POST',
        credentials: 'include',
      });
    } catch (error) {
      console.error('Failed to logout:', error);
    } finally {
      setUser(null);
      navigate({ to: '/login' });
    }
  };

  const register = async (email: string, password: string, full_name?: string) => {
    const response = await fetch(`${API_URL}/api/v1/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, full_name }),
    });

    if (response.ok) {
      // Redirect to verification page
      navigate({ to: '/verify-email' });
    } else {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Registration failed');
    }
  };

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    register,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}