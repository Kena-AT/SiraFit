"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useNavigate } from "@tanstack/react-router";
import { apiFetch } from "@/lib/api/client";

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

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const checkSession = async () => {
      try {
        const response = await apiFetch("/api/v1/users/me");
        if (response.ok) {
          const userData = await response.json();
          setUser(userData);
        }
      } catch {
        // Session expired or network error — user stays null
      } finally {
        setIsLoading(false);
      }
    };
    checkSession();
  }, []);

  const login = async (email: string, password: string) => {
    const response = await apiFetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username: email, password }),
    });

    if (response.ok) {
      const meResponse = await apiFetch("/api/v1/users/me");
      if (meResponse.ok) {
        const userData = await meResponse.json();
        setUser(userData);
      } else {
        throw new Error("Failed to fetch user details after login");
      }
    } else {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Login failed");
    }
  };

  const logout = async () => {
    try {
      await apiFetch("/api/v1/auth/logout", { method: "POST" });
    } catch {
      // Best-effort — clear state regardless
    } finally {
      setUser(null);
      navigate({ to: "/login" });
    }
  };

  const register = async (email: string, password: string, full_name?: string) => {
    const response = await apiFetch("/api/v1/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, full_name }),
    });

    if (response.ok) {
      navigate({ to: "/verify-email" });
    } else {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Registration failed");
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
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
