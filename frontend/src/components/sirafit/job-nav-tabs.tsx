import { Link, useRouterState } from "@tanstack/react-router";
import { cn } from "@/lib/utils";

export function JobNavTabs() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  const tabs = [
    { label: "Jobs Explorer", to: "/jobs" },
    { label: "Import jobs", to: "/jobs/import" },
    { label: "Import history", to: "/jobs/history" },
  ];

  return (
    <div className="flex items-center gap-1 border-b border-border pb-3 mb-6">
      {tabs.map((tab) => {
        const active =
          tab.to === "/jobs"
            ? pathname === "/jobs" || pathname === "/jobs/"
            : pathname.startsWith(tab.to);
        return (
          <Link
            key={tab.to}
            to={tab.to}
            className={cn(
              "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
              active
                ? "bg-muted text-foreground font-semibold"
                : "text-muted-foreground hover:bg-muted/50 hover:text-foreground",
            )}
          >
            {tab.label}
          </Link>
        );
      })}
    </div>
  );
}
