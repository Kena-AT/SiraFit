const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

let isRefreshing = false;
let refreshPromise: Promise<boolean> | null = null;

async function tryRefreshToken(): Promise<boolean> {
  // Deduplicate concurrent refresh attempts
  if (isRefreshing) return refreshPromise ?? Promise.resolve(false);

  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/auth/refresh-token`, {
        method: "POST",
        credentials: "include",
      });

      // Log for debugging
      if (!res.ok) {
        console.warn("Token refresh failed:", res.status, await res.text());
      }

      return res.ok;
    } catch (e) {
      console.error("Token refresh error:", e);
      return false;
    } finally {
      isRefreshing = false;
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
  }
}

// Flag to control automatic login redirect (disabled for beforeLoad hooks)
let shouldAutoRedirect = true;

export function setAutoRedirect(enabled: boolean) {
  shouldAutoRedirect = enabled;
}

/**
 * Navigate to login using the TanStack Router instance.
 * Lazy-imported to avoid circular deps — the router is created in router.tsx.
 */
async function navigateToLogin(): Promise<void> {
  if (!shouldAutoRedirect) return;

  try {
    const { getRouter } = await import("@/router");
    const router = getRouter();
    router.navigate({ to: "/login" });
  } catch {
    // Router not ready - do nothing. Let the caller handle navigation.
    // This can happen during SSR or very early client startup.
  }
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const url = path.startsWith("http") ? path : `${API_BASE_URL}${path}`;

  const mergedInit: RequestInit = {
    ...init,
    credentials: "include",
    headers: {
      ...(init.headers instanceof Headers
        ? Object.fromEntries(init.headers.entries())
        : Array.isArray(init.headers)
          ? Object.fromEntries(init.headers as [string, string][])
          : init.headers),
    },
  };

  let response = await fetch(url, mergedInit);

  if (response.status === 401) {
    console.log("Request returned 401, attempting token refresh...");
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      console.log("Token refreshed, retrying request...");
      response = await fetch(url, mergedInit);
    }
    if (response.status === 401) {
      console.log("Request still failed after refresh, redirecting to login");
      navigateToLogin();
      throw new ApiError(401, "Session expired. Please log in again.");
    }
  }

  return response;
}
