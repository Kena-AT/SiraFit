"use client";

import { Eye, EyeOff } from "lucide-react";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { AuthShell } from "@/components/sirafit/shell";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { OAuthButtons } from "@/components/auth/OAuthButtons";
import { TwoFactorVerify } from "@/components/auth/TwoFactorAuth";

export const Route = createFileRoute("/login")({
  head: () => ({ meta: [{ title: "Log in · SiraFit" }] }),
  component: LoginPage,
});

function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [twoFactorToken, setTwoFactorToken] = useState<string | null>(null);
  const { login, complete2FALogin } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    try {
      const result = await login(email, password);
      if (result.requires_2fa && result.temp_token) {
        setTwoFactorToken(result.temp_token);
      } else {
        navigate({ to: "/dashboard" });
      }
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handle2FASuccess = async () => {
    navigate({ to: "/dashboard" });
  };

  // Show 2FA verification screen
  if (twoFactorToken) {
    return (
      <AuthShell
        title="Two-Factor Authentication"
        subtitle="Enter the code from your authenticator app."
        footer={
          <button
            onClick={() => setTwoFactorToken(null)}
            className="font-medium text-foreground hover:underline"
          >
            Back to login
          </button>
        }
      >
        <TwoFactorVerify
          tempToken={twoFactorToken}
          onSuccess={handle2FASuccess}
          onBack={() => setTwoFactorToken(null)}
        />
      </AuthShell>
    );
  }

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Log in to your SiraFit dashboard."
      footer={
        <>
          No account?{" "}
          <Link to="/register" className="font-medium text-foreground hover:underline">
            Create one
          </Link>
          .
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && <div className="text-red-500 text-sm mb-4">{error}</div>}
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="king@kunta.dev"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <Label htmlFor="pwd">Password</Label>
            <Link
              to="/forgot-password"
              className="text-[11px] text-muted-foreground hover:text-foreground"
            >
              Forgot?
            </Link>
          </div>
          <div className="relative">
            <Input
              id="pwd"
              type={showPassword ? "text" : "password"}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
            >
              {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
            </button>
          </div>
        </div>
        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? "Logging in..." : "Log in"}
        </Button>
        <OAuthButtons mode="login" disabled={isLoading} />
        <div className="text-center text-[11px] text-muted-foreground">
          Protected by device-based auth tokens.
        </div>
      </form>
    </AuthShell>
  );
}
