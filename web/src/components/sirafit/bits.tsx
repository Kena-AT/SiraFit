"use client";

import Link from "next/link";
import { cn } from "@/lib/cn";
import type { ReactNode } from "react";

export function ScoreMeter({ value, className }: { value: number; className?: string }) {
  const tone =
    value >= 85
      ? "bg-emerald-500"
      : value >= 70
        ? "bg-amber-500"
        : "bg-muted-foreground/60";
  const text =
    value >= 85
      ? "text-emerald-600 dark:text-emerald-400"
      : value >= 70
        ? "text-amber-600 dark:text-amber-400"
        : "text-muted-foreground";
  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="h-1.5 w-16 overflow-hidden rounded-full bg-surface-hover border border-border">
        <div className={cn("h-full", tone)} style={{ width: `${Math.min(100, Math.max(0, value))}%` }} />
      </div>
      <span className={cn("font-mono text-xs font-semibold tabular-nums", text)}>{value}%</span>
    </div>
  );
}

export function ScorePill({ value }: { value: number }) {
  const cls =
    value >= 85
      ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
      : value >= 70
        ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30"
        : "bg-surface-hover text-muted border-border";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm px-1.5 py-0.5 font-mono text-[11px] font-semibold tabular-nums border",
        cls,
      )}
    >
      {value}%
    </span>
  );
}

const statusMap: Record<string, string> = {
  Saved: "bg-surface-hover text-muted border-border",
  Preparing: "bg-sky-500/10 text-sky-600 dark:text-sky-400 border-sky-500/30",
  Applied: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
  Assessment: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30",
  Interview: "bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/30",
  Offer: "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/40",
  Rejected: "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30",
  PROCEED: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/30",
  LOW_FRICTION: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/30",
  SKIP: "bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/30",
};

export function StatusPill({ status, className }: { status: string; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-sm px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider border",
        statusMap[status] ?? "bg-surface-hover text-muted border-border",
        className,
      )}
    >
      {status}
    </span>
  );
}

export function Tag({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm border border-border bg-surface px-1.5 py-0.5 font-mono text-[10px] text-muted",
        className,
      )}
    >
      {children}
    </span>
  );
}

export function Panel({
  children,
  className,
  title,
  action,
}: {
  children: ReactNode;
  className?: string;
  title?: string;
  action?: ReactNode;
}) {
  return (
    <div className={cn("rounded-xl border border-border bg-surface/70 p-5 shadow-xs backdrop-blur-xs", className)}>
      {title && (
        <div className="mb-4 flex items-center justify-between border-b border-border/60 pb-3">
          <h3 className="text-sm font-semibold tracking-tight text-foreground">{title}</h3>
          {action}
        </div>
      )}
      {children}
    </div>
  );
}

export function AgentDot({ status = "ready" }: { status?: "ready" | "busy" | "offline" }) {
  const colors = {
    ready: "bg-emerald-500 ring-emerald-500/30",
    busy: "bg-amber-500 ring-amber-500/30 animate-pulse",
    offline: "bg-muted ring-border",
  };
  return (
    <span className="relative flex h-2 w-2">
      <span className={cn("absolute inline-flex h-full w-full rounded-full opacity-75 ring-4", colors[status])} />
      <span className={cn("relative inline-flex h-2 w-2 rounded-full", colors[status])} />
    </span>
  );
}
