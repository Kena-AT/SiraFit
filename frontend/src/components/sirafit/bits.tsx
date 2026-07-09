import { Link } from "@tanstack/react-router";
import { cn } from "@/lib/utils";
import type { ReactNode } from "react";

export function ScoreMeter({ value, className }: { value: number; className?: string }) {
  const tone =
    value >= 85 ? "bg-[color:var(--success)]" : value >= 70 ? "bg-[color:var(--warning)]" : "bg-muted-foreground/60";
  const text =
    value >= 85 ? "text-[color:var(--success)]" : value >= 70 ? "text-[color:var(--warning)]" : "text-muted-foreground";
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="h-1.5 w-14 overflow-hidden rounded-full bg-muted">
        <div className={cn("h-full", tone)} style={{ width: `${value}%` }} />
      </div>
      <span className={cn("font-mono text-[11px] font-semibold tabular-nums", text)}>{value}</span>
    </div>
  );
}

export function ScorePill({ value }: { value: number }) {
  const cls =
    value >= 85
      ? "bg-[color:var(--success)]/10 text-[color:var(--success)] ring-[color:var(--success)]/20"
      : value >= 70
        ? "bg-[color:var(--warning)]/10 text-[color:var(--warning)] ring-[color:var(--warning)]/20"
        : "bg-muted text-muted-foreground ring-border";
  return (
    <span className={cn("inline-flex items-center rounded px-1.5 py-0.5 font-mono text-[11px] font-semibold tabular-nums ring-1", cls)}>
      {value}%
    </span>
  );
}

const statusMap: Record<string, string> = {
  Saved: "bg-muted text-muted-foreground ring-border",
  Preparing: "bg-[color:var(--info)]/10 text-[color:var(--info)] ring-[color:var(--info)]/20",
  Applied: "bg-[color:var(--brand)]/10 text-[color:var(--brand)] ring-[color:var(--brand)]/20",
  Assessment: "bg-[color:var(--warning)]/10 text-[color:var(--warning)] ring-[color:var(--warning)]/20",
  Interview: "bg-[color:var(--brand)]/15 text-[color:var(--brand)] ring-[color:var(--brand)]/30",
  "Final round": "bg-[color:var(--info)]/15 text-[color:var(--info)] ring-[color:var(--info)]/30",
  Offer: "bg-[color:var(--success)]/15 text-[color:var(--success)] ring-[color:var(--success)]/30",
  Rejected: "bg-destructive/10 text-destructive ring-destructive/20",
  Archived: "bg-muted text-muted-foreground ring-border",
  new: "bg-[color:var(--brand)]/10 text-[color:var(--brand)] ring-[color:var(--brand)]/20",
  saved: "bg-muted text-muted-foreground ring-border",
  seen: "bg-muted text-muted-foreground ring-border",
  applied: "bg-[color:var(--brand)]/10 text-[color:var(--brand)] ring-[color:var(--brand)]/20",
  success: "bg-[color:var(--success)]/10 text-[color:var(--success)] ring-[color:var(--success)]/20",
  info: "bg-[color:var(--info)]/10 text-[color:var(--info)] ring-[color:var(--info)]/20",
  warning: "bg-[color:var(--warning)]/10 text-[color:var(--warning)] ring-[color:var(--warning)]/20",
  muted: "bg-muted text-muted-foreground ring-border",
  completed: "bg-[color:var(--success)]/10 text-[color:var(--success)] ring-[color:var(--success)]/20",
  failed: "bg-destructive/10 text-destructive ring-destructive/20",
  // Sprint 9 application tracker statuses (snake_case from the status machine)
  preparing: "bg-[color:var(--info)]/10 text-[color:var(--info)] ring-[color:var(--info)]/20",
  screening: "bg-[color:var(--warning)]/10 text-[color:var(--warning)] ring-[color:var(--warning)]/20",
  interview: "bg-[color:var(--brand)]/15 text-[color:var(--brand)] ring-[color:var(--brand)]/30",
  final_round: "bg-[color:var(--info)]/15 text-[color:var(--info)] ring-[color:var(--info)]/30",
  offer: "bg-[color:var(--success)]/15 text-[color:var(--success)] ring-[color:var(--success)]/30",
  rejected: "bg-destructive/10 text-destructive ring-destructive/20",
  withdrawn: "bg-muted text-muted-foreground ring-border",
  archived: "bg-muted text-muted-foreground ring-border",
};

export function StatusPill({ status, className }: { status: string; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider ring-1",
        statusMap[status] ?? "bg-muted text-muted-foreground ring-border",
        className,
      )}
    >
      {status}
    </span>
  );
}

export function Tag({ children }: { children: ReactNode }) {
  return (
    <span className="inline-flex items-center rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] font-medium text-muted-foreground">
      {children}
    </span>
  );
}

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4 border-b border-border pb-5">
      <div>
        {eyebrow ? (
          <div className="mb-1 font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
            {eyebrow}
          </div>
        ) : null}
        <h1 className="text-xl font-semibold tracking-tight text-foreground">{title}</h1>
        {description ? <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{description}</p> : null}
      </div>
      {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
    </div>
  );
}

export function Panel({
  title,
  description,
  actions,
  children,
  className,
  bodyClassName,
}: {
  title?: string;
  description?: string;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  bodyClassName?: string;
}) {
  return (
    <section className={cn("overflow-hidden rounded-lg bg-card ring-1 ring-border", className)}>
      {(title || actions) && (
        <header className="flex items-center justify-between gap-4 border-b border-border bg-muted/30 px-4 py-2.5">
          <div>
            {title ? <h2 className="text-[13px] font-semibold tracking-tight text-foreground">{title}</h2> : null}
            {description ? <p className="text-[11px] text-muted-foreground">{description}</p> : null}
          </div>
          {actions ? <div className="flex items-center gap-1.5">{actions}</div> : null}
        </header>
      )}
      <div className={cn(bodyClassName)}>{children}</div>
    </section>
  );
}

export function Stat({
  label,
  value,
  trend,
  hint,
  mono = true,
}: {
  label: string;
  value: ReactNode;
  trend?: { value: string; positive?: boolean };
  hint?: string;
  mono?: boolean;
}) {
  return (
    <div className="rounded-lg bg-card p-4 ring-1 ring-border">
      <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">{label}</div>
      <div className={cn("mt-2 text-2xl font-semibold tracking-tight text-foreground", mono && "tabular-nums")}>{value}</div>
      {trend ? (
        <div
          className={cn(
            "mt-1 font-mono text-[10px] font-medium uppercase tracking-wider",
            trend.positive === false ? "text-destructive" : "text-[color:var(--success)]",
          )}
        >
          {trend.value}
        </div>
      ) : null}
      {hint ? <div className="mt-1 text-[11px] text-muted-foreground">{hint}</div> : null}
    </div>
  );
}

export function AgentDot({ label = "Local agent active" }: { label?: string }) {
  return (
    <span className="inline-flex items-center gap-1.5 font-mono text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
      <span className="relative inline-flex h-1.5 w-1.5">
        <span className="absolute inset-0 animate-ping rounded-full bg-[color:var(--brand)] opacity-60" />
        <span className="relative inline-block h-1.5 w-1.5 rounded-full bg-[color:var(--brand)]" />
      </span>
      {label}
    </span>
  );
}

export function Crumbs({ items }: { items: { label: string; to?: string }[] }) {
  return (
    <nav className="flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground">
      {items.map((it, i) => (
        <span key={i} className="inline-flex items-center gap-1.5">
          {it.to ? (
            <Link to={it.to} className="hover:text-foreground">
              {it.label}
            </Link>
          ) : (
            <span className={i === items.length - 1 ? "text-foreground" : ""}>{it.label}</span>
          )}
          {i < items.length - 1 ? <span className="text-border">/</span> : null}
        </span>
      ))}
    </nav>
  );
}

export function EmptyState({ title, body, action }: { title: string; body?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-border bg-muted/20 px-6 py-12 text-center">
      <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">EMPTY</div>
      <div className="text-sm font-medium text-foreground">{title}</div>
      {body ? <p className="max-w-sm text-xs text-muted-foreground">{body}</p> : null}
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  );
}