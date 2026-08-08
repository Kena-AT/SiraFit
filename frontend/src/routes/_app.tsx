import { createFileRoute, redirect } from "@tanstack/react-router";
import { AppShell } from "@/components/sirafit/shell";
import { apiFetch, ApiError, setAutoRedirect } from "@/lib/api/client";

export const Route = createFileRoute("/_app")({
  beforeLoad: async ({ context, location }) => {
    // Disable automatic login redirect during beforeLoad
    // We handle redirects explicitly to avoid double navigation
    setAutoRedirect(false);

    // Server-side auth check with cookie forwarding.
    // SSR runs without browser cookies — forward them via request headers.
    if (typeof window === "undefined") {
      // Access cookies from incoming request headers during SSR
      const requestHeaders = (await import("@tanstack/start-server-core")).getHeaders();
      const cookieHeader = requestHeaders.get("cookie");
      const accessToken = cookieHeader
        ?.split(";")
        .map((c) => c.trim())
        .find((c) => c.startsWith("access_token="))
        ?.split("=")[1];

      if (accessToken) {
        try {
          const res = await fetch("http://localhost:8000/api/v1/users/me", {
            headers: {
              Authorization: `Bearer ${accessToken}`,
            },
          });

          if (res.ok) {
            const user = await res.json();
            if (user.is_active) {
              return { user };
            }
          }
        } catch {
          // Fall through to redirect on error
        }
      }

      // No valid session — redirect to login server-side
      throw redirect({
        to: "/login",
        search: { redirect: location.href },
      });
    }

    // Client-side auth check (cookies available via same-origin proxy)
    try {
      const response = await apiFetch("/api/v1/users/me");

      if (!response.ok) {
        throw new Error("Not authenticated");
      }

      const user = await response.json();

      // Check if user is active (blocked accounts cannot access)
      if (!user.is_active) {
        throw new Error("Account inactive");
      }

      // Note: We allow unverified users to access the app
      // They'll see a verification banner prompting them to verify

      return { user };
    } catch (error: any) {
      if (error instanceof ApiError && error.status === 401) {
        throw redirect({
          to: "/login",
          search: {
            redirect: location.href,
          },
        });
      }
      // Session expired or other error - redirect to login
      throw redirect({
        to: "/login",
        search: {
          redirect: location.href,
        },
      });
    }
  },
  component: AppShell,
});
