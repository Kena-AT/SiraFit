import { createFileRoute, Outlet } from "@tanstack/react-router";
import { RouteErrorBoundary } from "@/components/sirafit/route-error";

export const Route = createFileRoute("/_app/jobs")({
  errorComponent: RouteErrorBoundary,
  component: () => <Outlet />,
});
