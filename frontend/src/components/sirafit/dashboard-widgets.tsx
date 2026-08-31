import { Link } from "@tanstack/react-router";
import { Panel } from "@/components/sirafit/bits";
import { cn } from "@/lib/utils";

/* ------------------------------------------------------------------ */
/* Shared helpers                                                       */
/* ------------------------------------------------------------------ */

export function timeAgo(iso: string): string {
  const d = new Date(iso).getTime();
  if (Number.isNaN(d)) return "";
  const diffM = Math.floor((Date.now() - d) / 60000);
  if (diffM < 1) return "just now";
  if (diffM < 60) return `${diffM}m ago`;
  const diffH = Math.floor(diffM / 60);
  if (diffH < 24) return `${diffH}h ago`;
  const diffD = Math.floor(diffH / 24);
  return `${diffD}d ago`;
}

export function WidgetSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-2 p-4">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-4 w-full animate-pulse rounded bg-muted" style={{ width: `${100 - i * 12}%` }} />
      ))}
    </div>
  );
}

export function WidgetError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div className="px-4 py-8 text-center">
      <div className="text-sm text-destructive">{message}</div>
      <button
        type="button"
        onClick={onRetry}
        className="mt-3 rounded-md border border-border px-3 py-1 text-xs font-medium hover:bg-muted"
      >
        Retry
      </button>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Stat card                                                            */
/* ------------------------------------------------------------------ */

export function StatCard({
  label,
  value,
  to,
  hint,
}: {
  label: string;
  value: number | string;
  to: string;
  hint?: string;
}) {
  return (
    <Link
      to={to}
      className="block rounded-lg border border-border bg-card p-4 transition-colors hover:bg-muted/40"
    >
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">{label}</div>
        <span className="text-xs text-muted-foreground">→</span>
      </div>
      <div className="mt-1 text-2xl font-bold tabular-nums">{value}</div>
      {hint ? <div className="mt-0.5 text-[11px] text-muted-foreground">{hint}</div> : null}
    </Link>
  );
}

/* ------------------------------------------------------------------ */
/* Search Momentum Score (#3)                                           */
/* ------------------------------------------------------------------ */

export function MomentumScore({ score, delta }: { score: number; delta: number }) {
  const tone =
    score >= 75 ? "var(--success)" : score >= 45 ? "var(--warning)" : "var(--destructive)";
  const circ = 2 * Math.PI * 42;
  return (
    <Panel
      title="Search momentum"
      description="Composite of weekly applications, follow-up punctuality, import cadence, and profile strength."
    >
      <div className="flex items-center gap-5 p-4">
        <div className="relative h-28 w-28 shrink-0">
          <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
            <circle cx="50" cy="50" r="42" fill="none" stroke="var(--border)" strokeWidth="9" />
            <circle
              cx="50"
              cy="50"
              r="42"
              fill="none"
              stroke={tone}
              strokeWidth="9"
              strokeLinecap="round"
              strokeDasharray={`${(score / 100) * circ} ${circ}`}
            />
          </svg>
          <div className="absolute inset-0 grid place-items-center">
            <div className="text-center">
              <div className="text-2xl font-bold tabular-nums">{score}</div>
              <div className="text-[9px] uppercase tracking-widest text-muted-foreground">/ 100</div>
            </div>
          </div>
        </div>
        <div className="min-w-0 space-y-1.5">
          {delta > 2 ? (
            <div className="text-sm font-medium text-[color:var(--success)]">▲ Trending up vs last week</div>
          ) : delta < -2 ? (
            <div className="text-sm font-medium text-destructive">▼ Slowing vs last week</div>
          ) : (
            <div className="text-sm font-medium text-muted-foreground">— Steady vs last week</div>
          )}
          <p className="text-xs text-muted-foreground">
            Consistent weekly activity is the strongest predictor of search success. Aim for 70+.
          </p>
        </div>
      </div>
    </Panel>
  );
}

/* ------------------------------------------------------------------ */
/* Pipeline funnel (#2)                                                 */
/* ------------------------------------------------------------------ */

export interface FunnelStage {
  label: string;
  value: number;
}

export function FunnelChart({ stages }: { stages: FunnelStage[] }) {
  const max = Math.max(...stages.map((s) => s.value), 1);
  return (
    <Panel title="Pipeline funnel" description="Where candidates drop off — click a stage to act.">
      <div className="space-y-3 p-4">
        {stages.map((s, i) => {
          const prev = i > 0 ? stages[i - 1].value : null;
          const conv = prev && prev > 0 ? Math.round((s.value * 100) / prev) : null;
          return (
            <div key={s.label}>
              <div className="mb-1 flex items-baseline justify-between text-sm">
                <span className="font-medium">{s.label}</span>
                <span className="flex items-center gap-2">
                  {conv !== null && (
                    <span
                      className={cn(
                        "font-mono text-[10px]",
                        conv >= 25 ? "text-[color:var(--success)]" : "text-muted-foreground",
                      )}
                    >
                      {conv}% conversion
                    </span>
                  )}
                  <span className="font-mono font-semibold tabular-nums">{s.value}</span>
                </span>
              </div>
              <div className="h-3 overflow-hidden rounded bg-muted">
                <div
                  className="h-full rounded bg-[color:var(--brand)] transition-all"
                  style={{ width: `${Math.max((s.value * 100) / max, s.value > 0 ? 6 : 0)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </Panel>
  );
}

/* ------------------------------------------------------------------ */
/* Response-rate sparkline (#6)                                         */
/* ------------------------------------------------------------------ */

export function ResponseSparkline({
  sent,
  responded,
}: {
  sent: number[];
  responded: number[];
}) {
  const weeks = sent.length;
  const maxVal = Math.max(...sent, ...responded, 1);
  const W = 260;
  const H = 56;
  const x = (i: number) => (weeks <= 1 ? W : (i * W) / (weeks - 1));
  const y = (v: number) => H - 4 - (v * (H - 10)) / maxVal;
  const path = (arr: number[]) =>
    arr.map((v, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");

  return (
    <Panel title="Response rate" description="Applications sent vs. responses received — trailing 8 weeks.">
      <div className="p-4">
        <svg viewBox={`0 0 ${W} ${H}`} className="h-14 w-full" preserveAspectRatio="none">
          <path d={path(sent)} fill="none" stroke="var(--muted-foreground)" strokeWidth="1.5" opacity="0.55" />
          <path d={path(responded)} fill="none" stroke="var(--success)" strokeWidth="2" />
        </svg>
        <div className="mt-2 flex items-center gap-4 text-[11px] text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-0.5 w-4 rounded bg-[color:var(--success)]" /> Responses
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-0.5 w-4 rounded bg-muted-foreground/60" /> Sent
          </span>
          <span className="ml-auto font-mono">8w → now</span>
        </div>
      </div>
    </Panel>
  );
}

/* ------------------------------------------------------------------ */
/* Next Best Action (#1)                                                */
/* ------------------------------------------------------------------ */

export interface NextAction {
  kind: "followup" | "review" | "skill" | "cadence" | "clear";
  title: string;
  body: string;
  cta: string;
  to: string;
}

const KIND_STYLES: Record<NextAction["kind"], string> = {
  followup: "bg-[color:var(--warning)]/10 text-[color:var(--warning)] ring-[color:var(--warning)]/20",
  review: "bg-[color:var(--brand)]/10 text-[color:var(--brand)] ring-[color:var(--brand)]/20",
  skill: "bg-[color:var(--info)]/10 text-[color:var(--info)] ring-[color:var(--info)]/20",
  cadence: "bg-muted text-muted-foreground ring-border",
  clear: "bg-[color:var(--success)]/10 text-[color:var(--success)] ring-[color:var(--success)]/20",
};

const KIND_LABEL: Record<NextAction["kind"], string> = {
  followup: "Overdue follow-up",
  review: "Review top match",
  skill: "Profile gap",
  cadence: "Keep importing",
  clear: "All clear",
};

export function NextBestActionCard({ action }: { action: NextAction | null }) {
  if (!action) return null;
  return (
    <Link
      to={action.to}
      className="block rounded-lg border border-border bg-card p-4 transition-colors hover:bg-muted/40"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <span
            className={cn(
              "inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wider ring-1",
              KIND_STYLES[action.kind],
            )}
          >
            {KIND_LABEL[action.kind]}
          </span>
          <div className="mt-1.5 font-semibold">{action.title}</div>
          <div className="text-sm text-muted-foreground">{action.body}</div>
        </div>
        <span className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background">
          {action.cta} →
        </span>
      </div>
    </Link>
  );
}

/* ------------------------------------------------------------------ */
/* Market pulse (#4)                                                    */
/* ------------------------------------------------------------------ */

export function MarketPulseWidget({
  totalAnalyzed,
  tags,
  profileSkills,
}: {
  totalAnalyzed: number;
  tags: { tag: string; count: number; pct: number }[];
  profileSkills: Set<string>;
}) {
  return (
    <Panel
      title="Market pulse"
      description={`Top skills across your ${totalAnalyzed} analyzed jobs — missing ones cap your match scores.`}
    >
      <div className="space-y-2 p-4">
        {tags.length === 0 ? (
          <div className="py-4 text-center text-sm text-muted-foreground">
            Import jobs with tags to unlock market insights.
          </div>
        ) : (
          tags.map(({ tag, count, pct }) => {
            const missing = !profileSkills.has(tag.toLowerCase());
            return (
              <div key={tag} className="flex items-center gap-3 text-sm">
                <div className="h-1.5 w-24 shrink-0 overflow-hidden rounded-full bg-muted">
                  <div className="h-full rounded bg-[color:var(--brand)]" style={{ width: `${Math.min(pct, 100)}%` }} />
                </div>
                <span className="font-mono text-[11px] tabular-nums text-muted-foreground w-10">
                  {pct}%
                </span>
                <span className="truncate font-medium">{tag}</span>
                {missing ? (
                  <span className="ml-auto shrink-0 rounded bg-[color:var(--warning)]/10 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-[color:var(--warning)] ring-1 ring-[color:var(--warning)]/20">
                    Missing in profile
                  </span>
                ) : (
                  <span className="ml-auto shrink-0 text-[10px] uppercase tracking-wider text-muted-foreground">
                    ✓ covered
                  </span>
                )}
              </div>
            );
          })
        )}
        <Link
          to="/resumes/profile-editor"
          className="mt-2 inline-block text-xs text-[color:var(--brand)] underline-offset-2 hover:underline"
        >
          Add missing skills to your profile →
        </Link>
      </div>
    </Panel>
  );
}
