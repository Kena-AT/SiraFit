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
  is_2fa_enabled?: boolean;
};

export type LoginResult = {
  requires_2fa?: boolean;
  challenge_token?: string;
  temp_token?: string;
  token_type?: string;
};

export type AuthContextType = {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<LoginResult>;
  logout: () => Promise<void>;
  register: (email: string, password: string, full_name?: string) => Promise<void>;
  complete2FALogin: (challengeToken: string, code: string) => Promise<void>;
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
        // Session expired or network error - user stays null
      } finally {
        setIsLoading(false);
      }
    };
    checkSession();
  }, []);

  const login = async (email: string, password: string): Promise<LoginResult> => {
    const response = await apiFetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (response.ok) {
      const data = await response.json();

      // Check if 2FA is required
      if (data.requires_2fa) {
        return {
          requires_2fa: true,
          challenge_token: data.challenge_token || data.temp_token,
          temp_token: data.temp_token || data.challenge_token,
          token_type: data.token_type,
        };
      }

      // Normal login — fetch user profile
      const meResponse = await apiFetch("/api/v1/users/me");
      if (meResponse.ok) {
        const userData = await meResponse.json();
        setUser(userData);
      } else {
        throw new Error("Failed to fetch user details after login");
      }
      return {};
    } else {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Login failed");
    }
  };

  const complete2FALogin = async (challengeToken: string, code: string) => {
    const response = await apiFetch("/api/v1/auth/2fa/login/verify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        challenge_token: challengeToken,
        temp_token: challengeToken,
        code,
      }),
    });

    if (response.ok) {
      const meResponse = await apiFetch("/api/v1/users/me");
      if (meResponse.ok) {
        const userData = await meResponse.json();
        setUser(userData);
      } else {
        throw new Error("Failed to fetch user details after 2FA");
      }
    } else {
      const errorData = await response.json();
      throw new Error(errorData.detail || "2FA verification failed");
    }
  };

  const logout = async () => {
    try {
      await apiFetch("/api/v1/auth/logout", { method: "POST" });
    } catch {
      // Best-effort - clear state regardless
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
      navigate({ to: "/verify-email", search: { email } });
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
    complete2FALogin,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    // Fallback safe guest state instead of throwing and crashing the render tree
    return {
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: async (): Promise<LoginResult> => ({}),
      logout: async () => {},
      register: async () => {},
      complete2FALogin: async () => {},
    };
  }
  return context;
}
