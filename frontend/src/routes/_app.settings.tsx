import { createFileRoute, Link, Outlet, useRouterState } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader } from "@/components/sirafit/bits";
import { cn } from "@/lib/utils";

const tabs = [
  { to: "/settings", label: "Account", match: "exact" as const },
  { to: "/settings/resume", label: "Resume" },
  { to: "/settings/ai", label: "AI & local agent" },
  { to: "/settings/notifications", label: "Notifications" },
  { to: "/settings/privacy", label: "Data & privacy" },
];

export const Route = createFileRoute("/_app/settings")({
  component: SettingsLayout,
});

function SettingsLayout() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  return (
    <PageBody>
      <PageHeader
        eyebrow="System"
        title="Settings"
        description="Account, agent, AI, notifications, and data preferences."
      />
      <nav className="flex flex-wrap gap-1 rounded-md bg-card p-1 ring-1 ring-border">
        {tabs.map((t) => {
          const active =
            t.match === "exact"
              ? pathname === t.to
              : pathname === t.to || pathname.startsWith(t.to + "/");
          return (
            <Link
              key={t.to}
              to={t.to}
              className={cn(
                "rounded px-3 py-1.5 text-[13px] font-medium",
                active
                  ? "bg-muted text-foreground ring-1 ring-border"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {t.label}
            </Link>
          );
        })}
      </nav>
      <Outlet />
    </PageBody>
  );
}
