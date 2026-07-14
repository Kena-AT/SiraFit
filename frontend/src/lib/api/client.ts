const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

let isRefreshing = false;
let refreshPromise: Promise<boolean> | null = null;

async function tryRefreshToken(): Promise<boolean> {
  if (isRefreshing && refreshPromise) return refreshPromise;

  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/auth/refresh-token`, {
        method: "POST",
        credentials: "include",
      });
      return res.ok;
    } catch {
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

/**
 * Navigate to login using the TanStack Router instance.
 * Lazy-imported to avoid circular deps — the router is created in router.tsx.
 */
async function navigateToLogin() {
  try {
    const { getRouter } = await import("@/router");
    const router = getRouter();
    router.navigate({ to: "/login" });
  } catch {
    // Fallback if router is unavailable (e.g. during SSR or before mount)
    window.location.href = "/login";
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
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      response = await fetch(url, mergedInit);
    }
    if (response.status === 401) {
      navigateToLogin();
      throw new ApiError(401, "Session expired. Please log in again.");
    }
  }

  return response;
}
