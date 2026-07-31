import { createFileRoute, redirect } from "@tanstack/react-router";
import { AppShell } from "@/components/sirafit/shell";

export const Route = createFileRoute("/_app")({
  beforeLoad: async ({ context, location }) => {
    // Check authentication status
    const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

    try {
      // First, try to refresh the access token (silent refresh)
      // Access tokens expire in 15 minutes; refresh token lasts 7 days
      await fetch(`${API_URL}/api/v1/auth/refresh-token`, {
        method: "POST",
        credentials: "include",
      });

      // Now fetch user with the (potentially refreshed) access token
      const response = await fetch(`${API_URL}/api/v1/users/me`, {
        credentials: "include",
      });

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
    } catch {
      // Session expired or network error - redirect to login with return path
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
