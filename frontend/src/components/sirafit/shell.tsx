import { Link, Outlet, useRouterState } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { AgentDot } from "./bits";

type NavItem = { label: string; to: string; badge?: string; match?: "exact" | "prefix" };
type NavGroup = { header: string; items: NavItem[] };

const NAV: NavGroup[] = [
  {
    header: "Operations",
    items: [
      { label: "Dashboard", to: "/dashboard", match: "exact" },
      { label: "Jobs Explorer", to: "/jobs" },
      { label: "Match Analysis", to: "/match" },
      { label: "Opportunity Ranking", to: "/ranking" },
      { label: "Batch Processing", to: "/batch" },
    ],
  },
  {
    header: "Pipeline",
    items: [
      { label: "Applications", to: "/applications" },
      { label: "Follow-ups", to: "/applications/followups", badge: "4" },
      { label: "Timeline", to: "/applications/timeline" },
    ],
  },
  {
    header: "Assets",
    items: [
      { label: "Resumes", to: "/resumes" },
      { label: "Profiles", to: "/resumes/profiles" },
      { label: "Resume Builder", to: "/resumes/builder" },
      { label: "Cover Letters", to: "/cover-letters" },
    ],
  },
  {
    header: "Intelligence",
    items: [
      { label: "Analytics", to: "/analytics" },
      { label: "Skill Insights", to: "/analytics/skills" },
      { label: "Market Insights", to: "/analytics/market" },
    ],
  },
  {
    header: "System",
    items: [
      { label: "Notifications", to: "/notifications", badge: "5" },
      { label: "Settings", to: "/settings" },
    ],
  },
];

function isActive(pathname: string, to: string, match: "exact" | "prefix" = "prefix") {
  if (match === "exact") return pathname === to;
  return pathname === to || pathname.startsWith(to + "/");
}

function Logo() {
  return (
    <div className="flex items-center gap-2">
      <div className="grid h-5 w-5 place-items-center rounded-sm bg-[color:var(--brand)] text-[10px] font-bold text-[color:var(--brand-foreground)] shadow-sm">
        S
      </div>
      <span className="text-sm font-semibold tracking-tight">SiraFit</span>
    </div>
  );
}

export function AppShell() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <div
      className="flex min-h-screen bg-background text-foreground"
      style={{ fontFamily: "'Inter', system-ui, sans-serif" }}
    >
      {/* Sidebar */}
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-border bg-sidebar md:flex">
        <div className="flex h-12 items-center justify-between border-b border-border px-4">
          <Link to="/dashboard">
            <Logo />
          </Link>
          <span className="font-mono text-[9px] font-medium uppercase tracking-widest text-muted-foreground">
            v0.8.2
          </span>
        </div>
        <nav className="flex-1 overflow-y-auto px-2 py-3">
          {NAV.map((group) => (
            <div key={group.header} className="mb-5">
              <div className="px-2 pb-1.5 font-mono text-[9px] font-semibold uppercase tracking-widest text-muted-foreground">
                {group.header}
              </div>
              <div className="flex flex-col gap-px">
                {group.items.map((item) => {
                  const active = isActive(pathname, item.to, item.match);
                  return (
                    <Link
                      key={item.to}
                      to={item.to}
                      className={cn(
                        "flex items-center justify-between rounded-md px-2 py-1.5 text-[13px] font-medium transition-colors",
                        active
                          ? "bg-sidebar-accent text-sidebar-accent-foreground ring-1 ring-border"
                          : "text-muted-foreground hover:bg-sidebar-accent/60 hover:text-foreground",
                      )}
                    >
                      <span className="flex items-center gap-2.5">
                        <span
                          className={cn(
                            "h-1.5 w-1.5 rounded-[1px]",
                            active ? "bg-[color:var(--brand)]" : "bg-border",
                          )}
                        />
                        {item.label}
                      </span>
                      {item.badge ? (
                        <span className="rounded bg-muted px-1.5 font-mono text-[10px] font-semibold text-muted-foreground">
                          {item.badge}
                        </span>
                      ) : null}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
        <div className="border-t border-border p-3">
          <div className="rounded-md bg-card p-3 ring-1 ring-border">
            <AgentDot label="Agent: connected" />
            <div className="mt-2 flex items-center justify-between text-[11px]">
              <span className="text-muted-foreground">Queue</span>
              <span className="font-mono font-semibold tabular-nums">3 / 64</span>
            </div>
            <div className="mt-1 flex items-center justify-between text-[11px]">
              <span className="text-muted-foreground">Last sync</span>
              <span className="font-mono tabular-nums">12s</span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar pathname={pathname} />
        <main className="flex-1 bg-muted/20">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function TopBar({ pathname }: { pathname: string }) {
  const segs = pathname.split("/").filter(Boolean);
  return (
    <header className="sticky top-0 z-20 flex h-12 items-center justify-between gap-4 border-b border-border bg-background/90 px-4 backdrop-blur md:px-6">
      <div className="flex items-center gap-3 md:hidden">
        <Logo />
      </div>
      <nav className="hidden items-center gap-1.5 text-[12px] font-medium text-muted-foreground md:flex">
        <Link to="/dashboard" className="hover:text-foreground">
          App
        </Link>
        {segs.map((s, i) => (
          <span key={i} className="inline-flex items-center gap-1.5">
            <span className="text-border">/</span>
            <span className={cn(i === segs.length - 1 ? "text-foreground" : "")}>
              {s.replace(/-/g, " ")}
            </span>
          </span>
        ))}
      </nav>
      <div className="ml-auto flex items-center gap-3">
        <div className="hidden h-7 items-center gap-2 rounded-md bg-card px-2.5 text-[11px] ring-1 ring-border md:flex">
          <span className="font-mono text-muted-foreground">⌘K</span>
          <span className="text-muted-foreground">Search jobs, apps, resumes…</span>
        </div>
        <AgentDot label="Gemini · connected" />
        <div className="grid h-7 w-7 place-items-center rounded-full bg-muted text-[11px] font-semibold ring-1 ring-border">
          AR
        </div>
      </div>
    </header>
  );
}

export function PageBody({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div className={cn("mx-auto w-full max-w-7xl space-y-6 px-4 py-6 md:px-6 md:py-8", className)}>
      {children}
    </div>
  );
}

export function MarketingShell({ children }: { children: ReactNode }) {
  return (
    <div
      className="min-h-screen bg-background text-foreground"
      style={{ fontFamily: "'Inter', system-ui, sans-serif" }}
    >
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <Link to="/">
            <Logo />
          </Link>
          <nav className="hidden gap-8 text-sm font-medium text-muted-foreground md:flex">
            <a href="#pipeline" className="hover:text-foreground">
              Pipeline
            </a>
            <a href="#intelligence" className="hover:text-foreground">
              Intelligence
            </a>
            <Link to="/help" className="hover:text-foreground">
              Docs
            </Link>
          </nav>
          <div className="flex items-center gap-2">
            <Link
              to="/login"
              className="rounded-md px-3 py-1.5 text-sm font-medium text-muted-foreground hover:text-foreground"
            >
              Log in
            </Link>
            <Link
              to="/dashboard"
              className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground transition-colors hover:bg-foreground/90"
            >
              Launch dashboard
            </Link>
          </div>
        </div>
      </header>
      {children}
      <footer className="border-t border-border bg-muted/20">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-6 py-6 text-[12px] text-muted-foreground">
          <div className="flex items-center gap-3">
            <Logo />
            <span>© {new Date().getFullYear()} SiraFit Labs.</span>
          </div>
          <div className="flex gap-5">
            <Link to="/privacy" className="hover:text-foreground">
              Privacy
            </Link>
            <Link to="/terms" className="hover:text-foreground">
              Terms
            </Link>
            <Link to="/help" className="hover:text-foreground">
              Help
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}

export function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <div
      className="grid min-h-screen bg-background text-foreground md:grid-cols-2"
      style={{ fontFamily: "'Inter', system-ui, sans-serif" }}
    >
      <div className="flex flex-col">
        <div className="flex items-center justify-between border-b border-border px-6 py-4">
          <Link to="/">
            <Logo />
          </Link>
          <AgentDot label="Local agent ready" />
        </div>
        <div className="flex flex-1 items-center justify-center px-6 py-12">
          <div className="w-full max-w-sm">
            <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
            {subtitle ? <p className="mt-2 text-sm text-muted-foreground">{subtitle}</p> : null}
            <div className="mt-8">{children}</div>
            {footer ? <div className="mt-8 text-[13px] text-muted-foreground">{footer}</div> : null}
          </div>
        </div>
      </div>
      <div className="hidden border-l border-border bg-[radial-gradient(circle_at_top_right,_color-mix(in_oklch,var(--brand)_15%,transparent),_transparent_60%)] md:block">
        <div className="flex h-full flex-col justify-between p-10">
          <div>
            <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
              Why SiraFit
            </div>
            <p className="mt-3 max-w-md text-[15px] leading-relaxed text-foreground">
              A career operations layer for engineers. Deterministic scoring, ATS-normalized data,
              and structured resume tailoring — without the autonomous-agent nonsense.
            </p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            {[
              ["842", "Jobs ingested today"],
              ["54", "Re-scored on profile change"],
              ["12", "ATS sources polled"],
              ["99.9%", "Local agent uptime"],
            ].map(([v, l]) => (
              <div key={l} className="rounded-md bg-card p-3 ring-1 ring-border">
                <div className="font-mono text-lg font-semibold tabular-nums">{v}</div>
                <div className="text-[11px] text-muted-foreground">{l}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
