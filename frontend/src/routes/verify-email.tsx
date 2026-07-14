import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { AuthShell } from "@/components/sirafit/shell";
import { Button } from "@/components/ui/button";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export const Route = createFileRoute("/verify-email")({
  head: () => ({ meta: [{ title: "Verify email · SiraFit" }] }),
  component: VerifyEmailPage,
});

function VerifyEmailPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  const handleResend = async () => {
    setIsLoading(true);
    setStatus(null);
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/resend-verification`, {
        method: "POST",
        credentials: "include",
      });
      if (!response.ok) {
        const err = await response
          .json()
          .catch(() => ({ detail: "Failed to resend verification" }));
        throw new Error(err.detail || "Failed to resend verification");
      }
      const data = await response.json();
      setStatus(data.detail || "Verification email resent");
    } catch (err: any) {
      setStatus(err.message || "Error resending verification email");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthShell
      title="Verify your email"
      subtitle="We sent a verification link to your email."
      footer={
        <>
          Didn't get it?{" "}
          <button
            type="button"
            className="font-medium text-foreground hover:underline"
            onClick={handleResend}
            disabled={isLoading}
          >
            {isLoading ? "Resending..." : "Resend"}
          </button>
        </>
      }
    >
      <div className="space-y-4">
        {status && (
          <div className={status.includes("error") ? "text-red-500" : "text-green-600"}>
            {status}
          </div>
        )}
        <Button asChild variant="link">
          <Link to="/login">Back to login</Link>
        </Button>
      </div>
    </AuthShell>
  );
}
