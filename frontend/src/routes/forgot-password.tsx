import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { AuthShell } from "@/components/sirafit/shell";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/forgot-password")({
  head: () => ({ meta: [{ title: "Reset password · SiraFit" }] }),
  component: ForgotPasswordPage,
});

function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setStatus("loading");
    setMessage("");

    try {
      const response = await fetch("/api/v1/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (response.ok) {
        setStatus("success");
        setMessage("If an account exists, a reset link has been sent to that email.");
      } else {
        setStatus("error");
        setMessage(data.detail || "Failed to request password reset.");
      }
    } catch (err) {
      setStatus("error");
      setMessage("A network error occurred. Please try again.");
    }
  };

  return (
    <AuthShell
      title="Reset your password"
      subtitle="We'll email a one-time reset link."
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
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input
              id="email"
              type="email"
              placeholder="you@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <Button type="submit" className="w-full" disabled={status === "loading"}>
            {status === "loading" ? "Sending..." : "Send reset link"}
          </Button>
        </form>
      )}
    </AuthShell>
  );
}