import { createFileRoute, Outlet } from "@tanstack/react-router";
import { MarketingShell } from "@/components/sirafit/shell";

export const Route = createFileRoute("/docs")({
  component: () => (
    <MarketingShell>
      <Outlet />
    </MarketingShell>
  ),
});