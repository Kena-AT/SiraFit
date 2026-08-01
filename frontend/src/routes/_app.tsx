import { createFileRoute, redirect } from "@tanstack/react-router";
import { AppShell } from "@/components/sirafit/shell";
import { apiFetch } from "@/lib/api/client";

export const Route = createFileRoute("/_app")({
  beforeLoad: async ({ context, location }) => {
    // Check authentication status
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
      // apiFetch calls navigateToLogin() on 401, which may have already navigated
      // We throw redirect to ensure TanStack Router handles it consistently
      if (error?.message === "Session expired. Please log in again." || error?.status === 401) {
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
