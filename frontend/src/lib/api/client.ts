// Same-origin by default: the Vite dev proxy forwards /api → backend:8000,
// so cookies are same-origin (Lax cookies work on plain HTTP). Set
// VITE_API_URL to an absolute URL only for cross-origin dev without a proxy.
const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

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

  // Determine if caller already provided a Content-Type header (case-insensitive)
  const hasContentType = init.headers && (
    (init.headers instanceof Headers && (init.headers.has("Content-Type") || init.headers.has("content-type"))) ||
    (Array.isArray(init.headers) && init.headers.some(([k]) => k.toLowerCase() === "content-type")) ||
    (typeof init.headers === "object" && Object.keys(init.headers).some(k => k.toLowerCase() === "content-type"))
  );

  const mergedInit: RequestInit = {
    ...init,
    credentials: "include",
    headers: {
      ...(init.headers instanceof Headers
        ? Object.fromEntries(init.headers.entries())
        : Array.isArray(init.headers)
          ? Object.fromEntries(init.headers as [string, string][])
          : init.headers),
      ...(hasContentType ? {} : { "Content-Type": "application/json" }), // Default only if not provided
    },
  };

  let response: Response;
  try {
    response = await fetch(url, mergedInit);
  } catch (e: any) {
    console.error("Network error during API fetch:", e.message);
    throw new ApiError(0, "Network error. Please check your connection.");
  }

  if (!response.ok) {
    let errorDetail = "An error occurred";
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorDetail;
    } catch {
      errorDetail = await response.text();
    }

    if (response.status === 401) {
      console.log("Request returned 401, attempting token refresh...");
      const refreshed = await tryRefreshToken();
      if (refreshed) {
        console.log("Token refreshed, retrying request...");
        try {
          response = await fetch(url, mergedInit);
          if (!response.ok) {
            throw new ApiError(response.status, errorDetail);
          }
          return response;
        } catch (e: any) {
          console.error("Error after token refresh:", e.message);
        }
      }
      console.log("Request still failed after refresh, redirecting to login");
      navigateToLogin();
      throw new ApiError(401, "Session expired. Please log in again.");
    }

    console.error(`API Error ${response.status}:`, errorDetail);
    throw new ApiError(response.status, errorDetail);
  }

  return response;
}
