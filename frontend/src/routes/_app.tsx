import { createFileRoute, redirect } from "@tanstack/react-router";
import { AppShell } from "@/components/sirafit/shell";

export const Route = createFileRoute("/_app")({
  beforeLoad: async ({ context, location }) => {
    // Check authentication status
    const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    
    try {
      const response = await fetch(`${API_URL}/api/v1/users/me`, {
        credentials: 'include',
      });
      
      if (!response.ok) {
        // Not authenticated, redirect to login
        throw redirect({
          to: '/login',
          search: {
            redirect: location.href,
          },
        });
      }
      
      const user = await response.json();
      
      // Check if user is active (blocked accounts cannot access)
      if (!user.is_active) {
        throw redirect({
          to: '/login',
        });
      }
      
      // Note: We allow unverified users to access the app
      // They'll see a verification banner prompting them to verify
      
      return { user };
    } catch (error) {
      if (error instanceof Response) {
        throw error; // Re-throw redirect responses
      }
      
      // Network or other error, redirect to login
      throw redirect({
        to: '/login',
        search: {
          redirect: location.href,
        },
      });
    }
  },
  component: AppShell,
});