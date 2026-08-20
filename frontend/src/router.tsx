import { QueryClient } from "@tanstack/react-query";
import { createRouter } from "@tanstack/react-router";
import { routeTree } from "./routeTree.gen";
import { ApiError } from "./lib/api/client";

export const getRouter = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        // Industry-standard 60s staleTime to prevent redundant refetches on navigation.
        staleTime: 60_000,
        gcTime: 10 * 60 * 1000,
        retry: (failureCount, error) => {
          if (error instanceof ApiError && error.status === 401) return false;
          return failureCount < 3;
        },
        refetchOnWindowFocus: false,
        refetchOnMount: false,
      },
      mutations: {
        retry: false,
      },
    },
  });

  const router = createRouter({
    routeTree,
    context: { queryClient },
    scrollRestoration: true,
    // Preload routes on hover/touch for instant navigation
    defaultPreload: "intent",
    defaultPreloadStaleTime: 60_000,
  });

  return router;
};
