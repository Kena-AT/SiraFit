import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getProfileHealth, getResumeHealth, ResumeHealthReport } from "@/lib/api/resumes";
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface ResumeHealthCardProps {
  resumeId?: string;
  versionId?: string;
  isProfile?: boolean;
}

export function ResumeHealthCard({ resumeId, versionId, isProfile }: ResumeHealthCardProps) {
  const [expanded, setExpanded] = useState(false);

  const {
    data: report,
    isLoading,
    error,
  } = useQuery<ResumeHealthReport>({
    queryKey: ["resume-health", isProfile ? "profile" : resumeId, versionId],
    queryFn: () => (isProfile ? getProfileHealth() : getResumeHealth(resumeId!, versionId)),
    enabled: isProfile || !!resumeId,
  });

  if (isLoading) {
    return (
      <div className="rounded-xl border border-border/70 bg-card p-4 space-y-2">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-border border-t-foreground" />
          Evaluating ATS Readiness & Health Score...
        </div>
      </div>
    );
  }

  if (error || !report) {
    return null;
  }

  const gradeColors: Record<string, { bg: string; text: string; border: string }> = {
    "A+": { bg: "bg-emerald-500/10", text: "text-emerald-500", border: "border-emerald-500/30" },
    A: { bg: "bg-emerald-500/10", text: "text-emerald-500", border: "border-emerald-500/30" },
    B: { bg: "bg-blue-500/10", text: "text-blue-500", border: "border-blue-500/30" },
    C: { bg: "bg-amber-500/10", text: "text-amber-500", border: "border-amber-500/30" },
    D: { bg: "bg-rose-500/10", text: "text-rose-500", border: "border-rose-500/30" },
  };

  const currentGrade = gradeColors[report.grade] || gradeColors.B;

  return (
    <div className="rounded-xl border border-border/80 bg-card p-5 space-y-4 shadow-xs">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-500 ring-1 ring-indigo-500/20 shrink-0">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-semibold text-foreground">ATS Readiness & Health</h3>
              <span
                className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-bold ring-1 ${currentGrade.bg} ${currentGrade.text} ${currentGrade.border}`}
              >
                Grade {report.grade}
              </span>
            </div>
            <p className="text-xs text-muted-foreground leading-relaxed">{report.summary}</p>
          </div>
        </div>

        {/* Big score circle */}
        <div className="text-right shrink-0">
          <div className="font-mono text-2xl font-black text-foreground">
            {report.overall_score}
            <span className="text-xs font-normal text-muted-foreground">/100</span>
          </div>
          <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Health Score
          </div>
        </div>
      </div>

      {/* Category breakdown bars */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-2 border-t border-border/60">
        <div>
          <div className="flex justify-between text-[10px] font-medium text-muted-foreground mb-1">
            <span>Completeness</span>
            <span>{report.breakdown.completeness}/25</span>
          </div>
          <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
            <div
              className="h-full bg-blue-500 rounded-full"
              style={{ width: `${(report.breakdown.completeness / 25) * 100}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-[10px] font-medium text-muted-foreground mb-1">
            <span>Action Verbs</span>
            <span>{report.breakdown.action_verbs}/25</span>
          </div>
          <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
            <div
              className="h-full bg-indigo-500 rounded-full"
              style={{ width: `${(report.breakdown.action_verbs / 25) * 100}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-[10px] font-medium text-muted-foreground mb-1">
            <span>Metrics</span>
            <span>{report.breakdown.quantified_metrics}/25</span>
          </div>
          <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
            <div
              className="h-full bg-emerald-500 rounded-full"
              style={{ width: `${(report.breakdown.quantified_metrics / 25) * 100}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-[10px] font-medium text-muted-foreground mb-1">
            <span>Formatting</span>
            <span>{report.breakdown.formatting}/15</span>
          </div>
          <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
            <div
              className="h-full bg-purple-500 rounded-full"
              style={{ width: `${(report.breakdown.formatting / 15) * 100}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between text-[10px] font-medium text-muted-foreground mb-1">
            <span>Skills Depth</span>
            <span>{report.breakdown.skills_richness}/10</span>
          </div>
          <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
            <div
              className="h-full bg-amber-500 rounded-full"
              style={{ width: `${(report.breakdown.skills_richness / 10) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {/* Expand/Collapse Checklist */}
      <div className="pt-2">
        <Button
          variant="ghost"
          size="sm"
          className="h-7 w-full text-xs text-muted-foreground hover:text-foreground justify-between px-2"
          onClick={() => setExpanded((v) => !v)}
        >
          <span>
            {expanded
              ? "Hide diagnostic details"
              : `View ${report.checks.length} diagnostic checks`}
          </span>
          {expanded ? (
            <ChevronUp className="h-3.5 w-3.5" />
          ) : (
            <ChevronDown className="h-3.5 w-3.5" />
          )}
        </Button>

        {expanded && (
          <div className="mt-3 space-y-2.5 pt-2 border-t border-border/50 text-xs">
            <div className="space-y-2">
              {report.checks.map((check, i) => (
                <div key={i} className="flex items-start gap-2.5 p-2 rounded-lg bg-muted/40">
                  {check.passed ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                  ) : (
                    <AlertTriangle className="h-4 w-4 text-amber-500 shrink-0 mt-0.5" />
                  )}
                  <div className="space-y-0.5 flex-1">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-foreground">{check.title}</span>
                      <span className="font-mono text-[10px] text-muted-foreground">
                        {check.score}/{check.max_score}
                      </span>
                    </div>
                    <p className="text-[11px] text-muted-foreground leading-snug">
                      {check.feedback}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {report.recommendations.length > 0 && (
              <div className="rounded-lg border border-indigo-500/20 bg-indigo-500/5 p-3 space-y-1.5 mt-3">
                <div className="flex items-center gap-1.5 font-medium text-indigo-600 dark:text-indigo-400 text-xs">
                  <TrendingUp className="h-3.5 w-3.5" />
                  <span>Actionable Optimization Recommendations</span>
                </div>
                <ul className="space-y-1 pl-4 list-disc text-[11px] text-foreground/90">
                  {report.recommendations.map((rec, idx) => (
                    <li key={idx} className="leading-relaxed">
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
