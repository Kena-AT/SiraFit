"use client";

import { useState } from "react";
import { ShieldCheck, CheckCircle2, ChevronDown, ChevronUp, Sparkles, AlertCircle } from "lucide-react";
import { Panel } from "./bits";
import type { ResumeHealthReport } from "@/lib/sirafit-engine";

export interface ResumeHealthCardProps {
  report: ResumeHealthReport;
  onRefresh?: () => void;
  className?: string;
}

export function ResumeHealthCard({ report, onRefresh, className }: ResumeHealthCardProps) {
  const [expanded, setExpanded] = useState(false);

  const gradeColors: Record<string, { bg: string; text: string; border: string }> = {
    "A+": { bg: "bg-emerald-500/10", text: "text-emerald-500", border: "border-emerald-500/30" },
    A: { bg: "bg-emerald-500/10", text: "text-emerald-500", border: "border-emerald-500/30" },
    B: { bg: "bg-sky-500/10", text: "text-sky-500", border: "border-sky-500/30" },
    C: { bg: "bg-amber-500/10", text: "text-amber-500", border: "border-amber-500/30" },
    D: { bg: "bg-rose-500/10", text: "text-rose-500", border: "border-rose-500/30" },
  };

  const currentGrade = gradeColors[report.grade] || gradeColors.B;

  return (
    <Panel className={className}>
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <ShieldCheck className="size-4 text-emerald-500" />
            <h3 className="text-sm font-semibold tracking-tight text-foreground">
              ATS Readiness & Resume Health
            </h3>
            <span className={`rounded-md px-2 py-0.5 text-xs font-bold border ${currentGrade.bg} ${currentGrade.text} ${currentGrade.border}`}>
              Grade {report.grade}
            </span>
          </div>
          <p className="text-xs text-muted">{report.summary}</p>
        </div>

        <div className="text-right">
          <div className="text-2xl font-black tabular-nums text-foreground">
            {report.overallScore}
            <span className="text-xs font-normal text-muted">/100</span>
          </div>
        </div>
      </div>

      {/* 5-pillar metric bars */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 pt-3 border-t border-border">
        {Object.entries(report.breakdown).map(([key, val]) => (
          <div key={key} className="space-y-1">
            <div className="flex justify-between text-[11px] text-muted capitalize">
              <span>{key.replace(/([A-Z])/g, ' $1')}</span>
              <span className="font-mono font-semibold">{val}</span>
            </div>
            <div className="h-1.5 w-full bg-surface-hover rounded-full overflow-hidden border border-border/40">
              <div
                className="h-full bg-emerald-500 rounded-full"
                style={{ width: `${(val / 25) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Expandable checklist & recommendations */}
      <div className="pt-2">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1.5 text-xs font-medium text-brand hover:underline"
        >
          {expanded ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />}
          {expanded ? "Hide Audit Checks & Action Items" : "View Detailed ATS Checks & Recommendations"}
        </button>

        {expanded && (
          <div className="mt-4 space-y-4 pt-3 border-t border-border text-xs">
            <div className="space-y-2">
              <h4 className="font-semibold text-foreground flex items-center gap-1.5">
                <CheckCircle2 className="size-3.5 text-emerald-500" />
                Audit Criteria
              </h4>
              <div className="grid gap-2 sm:grid-cols-2">
                {report.checks.map((c, i) => (
                  <div
                    key={i}
                    className="p-2.5 rounded-lg border border-border bg-surface-hover/50 space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-foreground">{c.title}</span>
                      <span className="font-mono text-[10px] text-muted">
                        {c.score}/{c.maxScore}
                      </span>
                    </div>
                    <p className="text-[11px] text-muted leading-relaxed">{c.feedback}</p>
                  </div>
                ))}
              </div>
            </div>

            {report.recommendations.length > 0 && (
              <div className="space-y-2">
                <h4 className="font-semibold text-foreground flex items-center gap-1.5">
                  <Sparkles className="size-3.5 text-amber-500" />
                  Actionable Recommendations
                </h4>
                <ul className="space-y-1.5 pl-4 list-disc text-muted leading-relaxed">
                  {report.recommendations.map((rec, i) => (
                    <li key={i}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </Panel>
  );
}
