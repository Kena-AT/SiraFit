import { cn } from "@/lib/utils";
import type { JobAnalysis } from "@/types/job";

// ---------------------------------------------------------------------------
// Score ring
// ---------------------------------------------------------------------------

function ScoreRing({ score }: { score: number }) {
  const size = 80;
  const strokeW = 7;
  const radius = (size - strokeW) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const color =
    score >= 75 ? "var(--success, #22c55e)" :
    score >= 50 ? "var(--warning, #f59e0b)" :
    "var(--destructive, #ef4444)";

  return (
    <div className="flex flex-col items-center gap-1">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
          {/* Track */}
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth={strokeW}
            className="text-border"
          />
          {/* Progress */}
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeW}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: "stroke-dashoffset 0.6s ease" }}
          />
        </svg>
        {/* Score label */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-bold tabular-nums leading-none" style={{ color }}>
            {score}
          </span>
          <span className="text-[9px] font-semibold uppercase tracking-widest text-muted-foreground">
            /100
          </span>
        </div>
      </div>
      <span className="text-[11px] font-medium text-muted-foreground">Match score</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// List rows
// ---------------------------------------------------------------------------

function ListSection({
  title, items, variant,
}: { title: string; items: string[]; variant: "pro" | "con" | "gap" | "req" }) {
  if (!items || items.length === 0) return null;

  const iconClass = {
    pro: "text-[color:var(--success,#22c55e)]",
    con: "text-destructive",
    gap: "text-[color:var(--warning,#f59e0b)]",
    req: "text-muted-foreground",
  }[variant];

  const icon = {
    pro: "✓",
    con: "✗",
    gap: "△",
    req: "·",
  }[variant];

  return (
    <div>
      <div className="mb-1.5 font-mono text-[9px] font-semibold uppercase tracking-widest text-muted-foreground">
        {title}
      </div>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-[12px]">
            <span className={cn("shrink-0 font-bold leading-[1.4]", iconClass)}>{icon}</span>
            <span className="text-foreground/90">{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Skeleton
// ---------------------------------------------------------------------------

export function AnalysisSkeleton() {
  return (
    <div className="space-y-4 p-4 animate-pulse">
      <div className="flex justify-center">
        <div className="h-20 w-20 rounded-full bg-muted" />
      </div>
      {[80, 60, 95, 70].map((w, i) => (
        <div key={i} className="h-3 rounded bg-muted" style={{ width: `${w}%` }} />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export function AnalysisInsights({ analysis }: { analysis: JobAnalysis }) {
  return (
    <div className="space-y-5 p-4">
      {/* Header: score ring + seniority */}
      <div className="flex items-center justify-between">
        <ScoreRing score={analysis.score} />
        {analysis.seniority && (
          <div className="text-right">
            <div className="font-mono text-[9px] font-semibold uppercase tracking-widest text-muted-foreground mb-0.5">
              Seniority
            </div>
            <span className="inline-flex items-center rounded-md bg-muted px-2 py-0.5 font-mono text-[11px] font-semibold ring-1 ring-border">
              {analysis.seniority}
            </span>
          </div>
        )}
      </div>

      {/* Summary */}
      {analysis.summary && (
        <p className="text-[12px] text-foreground/80 leading-relaxed border-t border-border pt-4">
          {analysis.summary}
        </p>
      )}

      <div className="space-y-4 border-t border-border pt-4">
        <ListSection title="Strengths" items={analysis.pros} variant="pro" />
        <ListSection title="Weaknesses" items={analysis.cons} variant="con" />
        <ListSection title="Skills gap" items={analysis.skills_gap} variant="gap" />
        <ListSection title="Key requirements" items={analysis.key_requirements} variant="req" />
      </div>

      {/* Footer */}
      <div className="border-t border-border pt-3 text-[10px] text-muted-foreground">
        Prompt {analysis.analysis_version ?? "v1"} · Generated by AI
      </div>
    </div>
  );
}
