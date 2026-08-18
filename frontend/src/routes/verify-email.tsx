import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { AuthShell } from "@/components/sirafit/shell";
import { Button } from "@/components/ui/button";
import { apiFetch, ApiError } from "@/lib/api/client";

type VerifyEmailSearch = {
  token?: string;
  email?: string;
};

export const Route = createFileRoute("/verify-email")({
  head: () => ({ meta: [{ title: "Verify email · SiraFit" }] }),
  validateSearch: (search: Record<string, unknown>): VerifyEmailSearch => {
    return {
      token: typeof search.token === "string" ? search.token : undefined,
      email: typeof search.email === "string" ? search.email : undefined,
    };
  },
  component: VerifyEmailPage,
});

type VerifyState = "idle" | "loading" | "success" | "error";

function VerifyEmailPage() {
  const search = Route.useSearch();
  const navigate = useNavigate();

  // ── Token flow: user clicked the link from email ─────────────────────────
  const [verifyState, setVerifyState] = useState<VerifyState>(
    search.token ? "loading" : "idle",
  );
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!search.token) return;

    const verify = async () => {
      try {
        const res = await apiFetch("/api/v1/auth/verify-email", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token: search.token }),
        });

        setVerifyState("success");
      } catch (err) {
        if (err instanceof ApiError) {
          setErrorMessage(err.message || "The verification link is invalid or has expired.");
        } else {
          setErrorMessage("Could not connect to the server. Please try again.");
        }
        setVerifyState("error");
      }
    };

    verify();
  }, [search.token]);

  // ── Success screen ────────────────────────────────────────────────────────
  if (verifyState === "success") {
    return (
      <AuthShell title="Email verified!">
        <div className="flex flex-col items-center gap-6 text-center">
          {/* Animated checkmark circle */}
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-emerald-50 ring-8 ring-emerald-50 dark:bg-emerald-950/30 dark:ring-emerald-950/30">
            <svg
              className="h-10 w-10 text-emerald-500"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2.5}
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M20 6 9 17l-5-5" />
            </svg>
          </div>

          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              Your email address has been verified successfully. Your account is
              now fully active and ready to use.
            </p>
          </div>

          <div className="flex w-full flex-col gap-3">
            <Button
              className="w-full"
              onClick={() => navigate({ to: "/login" })}
            >
              Continue to login
            </Button>
            <Button variant="outline" className="w-full" asChild>
              <Link to="/dashboard">Go to dashboard</Link>
            </Button>
          </div>
        </div>
      </AuthShell>
    );
  }

  // ── Error screen ──────────────────────────────────────────────────────────
  if (verifyState === "error") {
    return (
      <AuthShell
        title="Verification failed"
        subtitle={errorMessage ?? "Something went wrong."}
      >
        <div className="flex flex-col items-center gap-6 text-center">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-red-50 ring-8 ring-red-50 dark:bg-red-950/30 dark:ring-red-950/30">
            <svg
              className="h-10 w-10 text-red-500"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={2.5}
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="m15 9-6 6M9 9l6 6" />
            </svg>
          </div>

          <div className="flex w-full flex-col gap-3">
            <Button
              className="w-full"
              onClick={() =>
                navigate({ to: "/verify-email", search: { email: "" } })
              }
            >
              Request a new link
            </Button>
            <Button variant="outline" className="w-full" asChild>
              <Link to="/login">Back to login</Link>
            </Button>
          </div>
        </div>
      </AuthShell>
    );
  }

  // ── Loading screen (token present, verifying…) ────────────────────────────
  if (verifyState === "loading") {
    return (
      <AuthShell title="Verifying your email…" subtitle="Just a moment.">
        <div className="flex justify-center py-8">
          <svg
            className="h-10 w-10 animate-spin text-muted-foreground"
            viewBox="0 0 24 24"
            fill="none"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8v4l3-3-3-3V0a12 12 0 100 24v-4l-3 3 3 3v4A12 12 0 014 12z"
            />
          </svg>
        </div>
      </AuthShell>
    );
  }

  // ── Idle: "check your inbox" screen ──────────────────────────────────────
  return <WaitingForVerification email={search.email} />;
}

function WaitingForVerification({ email }: { email?: string }) {
  const [inputEmail, setInputEmail] = useState(email || "");
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleResend = async () => {
    if (!inputEmail) {
      setStatus({ type: "error", text: "Please enter your email address." });
      return;
    }
    setIsLoading(true);
    setStatus(null);
    try {
      const res = await apiFetch("/api/v1/auth/resend-verification", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: inputEmail }),
      });
      const data = await res.json();
      setStatus({ type: "success", text: data.detail || "Verification email sent!" });
    } catch (err) {
      if (err instanceof ApiError) {
        setStatus({ type: "error", text: err.message || "Failed to resend." });
      } else {
        setStatus({ type: "error", text: "Network error. Please try again." });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthShell
      title="Verify your email"
      subtitle={
        email
          ? `We sent a verification link to ${email}.`
          : "We sent a verification link to your email."
      }
      footer={
        <>
          Didn't get it?{" "}
          <button
            type="button"
            className="font-medium text-foreground hover:underline"
            onClick={handleResend}
            disabled={isLoading}
          >
            {isLoading ? "Resending…" : "Resend"}
          </button>
        </>
      }
    >
      <div className="space-y-4">
        {/* Envelope illustration */}
        <div className="flex justify-center py-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted ring-8 ring-muted">
            <svg
              className="h-8 w-8 text-muted-foreground"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth={1.5}
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect width="20" height="16" x="2" y="4" rx="2" />
              <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
            </svg>
          </div>
        </div>

        {/* Show email input only if the email wasn't passed in the URL */}
        {!email && (
          <div className="flex flex-col space-y-2">
            <label htmlFor="email" className="text-sm font-medium">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              value={inputEmail}
              onChange={(e) => setInputEmail(e.target.value)}
              placeholder="Enter your email"
            />
          </div>
        )}

        {status && (
          <p
            className={`text-sm ${status.type === "error" ? "text-red-500" : "text-emerald-600"}`}
          >
            {status.text}
          </p>
        )}

        <Button variant="outline" className="w-full" asChild>
          <Link to="/login">Back to login</Link>
        </Button>
      </div>
    </AuthShell>
  );
}
