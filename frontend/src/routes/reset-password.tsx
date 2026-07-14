import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { AuthShell } from "@/components/sirafit/shell";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

type ResetPasswordSearch = {
  token?: string;
};

export const Route = createFileRoute("/reset-password")({
  validateSearch: (search: Record<string, unknown>): ResetPasswordSearch => ({
    token: typeof search.token === "string" ? search.token : undefined,
  }),
  head: () => ({ meta: [{ title: "Set new password · SiraFit" }] }),
  component: ResetPasswordPage,
});

function ResetPasswordPage() {
  const { token } = Route.useSearch();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password || password !== confirmPassword) {
      setStatus("error");
      setMessage("Passwords do not match.");
      return;
    }
    if (!token) {
      setStatus("error");
      setMessage("Missing or invalid reset token.");
      return;
    }

    setStatus("loading");
    setMessage("");

    try {
      const response = await fetch("/api/v1/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });

      const data = await response.json();

      if (response.ok) {
        setStatus("success");
        setMessage("Password has been reset successfully. Redirecting to login...");
        setTimeout(() => {
          navigate({ to: "/login" });
        }, 2000);
      } else {
        setStatus("error");
        setMessage(data.detail || "Failed to reset password.");
      }
    } catch (err) {
      setStatus("error");
      setMessage("A network error occurred. Please try again.");
    }
  };

  return (
    <AuthShell
      title="Set a new password"
      subtitle="Use 12+ characters with at least one number."
      footer={
        <Link to="/login" className="font-medium text-foreground hover:underline">
          Back to login
        </Link>
      }
    >
      {status === "success" ? (
        <div className="p-4 bg-green-50 text-green-700 rounded-md border border-green-200 text-sm text-center">
          {message}
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          {status === "error" && (
            <div className="p-3 bg-red-50 text-red-600 rounded-md border border-red-200 text-sm text-center">
              {message}
            </div>
          )}
          {!token && status !== "error" && (
            <div className="p-3 bg-yellow-50 text-yellow-700 rounded-md border border-yellow-200 text-sm text-center mb-4">
              Missing reset token in URL. Please use the link sent to your email.
            </div>
          )}
          <div className="space-y-1.5">
            <Label htmlFor="p1">New password</Label>
            <Input
              id="p1"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="p2">Confirm password</Label>
            <Input
              id="p2"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>
          <Button type="submit" className="w-full" disabled={status === "loading" || !token}>
            {status === "loading" ? "Updating..." : "Update password"}
          </Button>
        </form>
      )}
    </AuthShell>
  );
}
