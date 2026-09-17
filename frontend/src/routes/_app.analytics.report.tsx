import { useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel } from "@/components/sirafit/bits";
import {
  getAnalyticsMetrics,
  downloadAnalyticsExport,
  type SalaryBenchmark,
  type SkillGapItem,
  type StageInsight,
} from "@/lib/api/analytics";

export const Route = createFileRoute("/_app/analytics/report")({
  head: () => ({ meta: [{ title: "Executive Analytics Report · SiraFit" }] }),
  component: AnalyticsReportView,
});

function AnalyticsReportView() {
  const [isExporting, setIsExporting] = useState(false);

  const {
    data: metrics,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["analytics-metrics"],
    queryFn: getAnalyticsMetrics,
    staleTime: 60000,
  });

  const handleExport = async () => {
    try {
      setIsExporting(true);
      await downloadAnalyticsExport("xlsx");
    } catch (err: unknown) {
      console.error("Export failed:", err);
    } finally {
      setIsExporting(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (isLoading) {
    return (
      <PageBody>
        <PageHeader eyebrow="Intelligence" title="Analytics Report" description="Loading report..." />
        <div className="grid place-items-center py-20 text-muted-foreground">Loading report...</div>
      </PageBody>
    );
  }

  if (error) {
    return (
      <PageBody>
        <PageHeader eyebrow="Intelligence" title="Analytics Report" description="Failed to load report" />
        <div className="px-4 py-8 text-center text-sm text-destructive">{error.message}</div>
      </PageBody>
    );
  }

  const salaryBenchmarks: SalaryBenchmark[] = metrics?.salary_benchmarks || [];
  const skillsGapItems: SkillGapItem[] = metrics?.skills_gap_analysis?.skills || [];
  const stallStages: StageInsight[] = metrics?.stall_insights?.stages || [];

  return (
    <PageBody>
      <div className="print:hidden">
        <PageHeader
          eyebrow="Authenticated Intelligence"
          title="Executive Analytics Report"
          description="Comprehensive recruitment funnel, market salary benchmarks, and skill readiness."
          actions={
            <div className="flex items-center gap-2">
              <button
                onClick={handlePrint}
                className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted transition-colors"
              >
                Print / Save as PDF
              </button>
              <button
                onClick={handleExport}
                disabled={isExporting}
                className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted disabled:opacity-50 transition-colors"
              >
                {isExporting ? "Exporting..." : "Download Excel"}
              </button>
              <Link
                to="/analytics"
                className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted transition-colors"
              >
                Back to Dashboard
              </Link>
            </div>
          }
        />
      </div>

      {/* Printable Report Header */}
      <div className="mb-6 rounded-lg border border-border bg-card p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-border pb-4">
          <div>
            <h1 className="text-xl font-bold tracking-tight text-foreground">SiraFit Career Analytics & Market Report</h1>
            <p className="text-xs text-muted-foreground">Deterministic insights derived from your pipeline status events and imported job metadata.</p>
          </div>
          <div className="text-xs font-mono text-muted-foreground sm:text-right">
            <div>Report Date: {metrics?.generated_at ? new Date(metrics.generated_at).toLocaleDateString() : "Current"}</div>
            <div>Source: SiraFit Unified Engine</div>
          </div>
        </div>

        {/* Executive Summary Metrics */}
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="rounded border border-border/60 bg-muted/20 p-3">
            <div className="text-[11px] font-medium text-muted-foreground uppercase">Total Applications</div>
            <div className="text-2xl font-bold font-mono mt-1">{metrics?.total_applications ?? 0}</div>
          </div>
          <div className="rounded border border-border/60 bg-muted/20 p-3">
            <div className="text-[11px] font-medium text-muted-foreground uppercase">Interview Rate</div>
            <div className="text-2xl font-bold font-mono mt-1">{metrics?.interview_rate?.toFixed(1) ?? 0}%</div>
          </div>
          <div className="rounded border border-border/60 bg-muted/20 p-3">
            <div className="text-[11px] font-medium text-muted-foreground uppercase">Offer Rate</div>
            <div className="text-2xl font-bold font-mono mt-1">{metrics?.offer_rate?.toFixed(1) ?? 0}%</div>
          </div>
          <div className="rounded border border-border/60 bg-muted/20 p-3">
            <div className="text-[11px] font-medium text-muted-foreground uppercase">Avg Response Time</div>
            <div className="text-2xl font-bold font-mono mt-1">{metrics?.avg_response_time_days?.toFixed(1) ?? 0}d</div>
          </div>
        </div>
      </div>

      {/* Pipeline & Stage Stall Section */}
      <Panel title="1. Stage Duration & Drop-Off Analysis">
        <div className="p-4">
          <p className="text-xs text-muted-foreground mb-3">
            Stage dwell times and drop-off rates are calculated exclusively from verified transitions in the application timeline. Dwell medians require at least 3 completed observations.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border text-[11px] uppercase tracking-wider text-muted-foreground font-mono">
                <tr>
                  <th className="pb-2 font-medium">Stage</th>
                  <th className="pb-2 font-medium">Entered</th>
                  <th className="pb-2 font-medium">Progressed</th>
                  <th className="pb-2 font-medium">Dropped</th>
                  <th className="pb-2 font-medium">Drop-off Rate</th>
                  <th className="pb-2 font-medium">Median Duration</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border font-mono text-xs">
                {stallStages.map((st) => (
                  <tr key={st.stage} className="hover:bg-muted/30">
                    <td className="py-2.5 font-sans font-medium capitalize">{st.stage.replace("_", " ")}</td>
                    <td className="py-2.5">{st.entered_count}</td>
                    <td className="py-2.5 text-[color:var(--brand)]">{st.progressed_count}</td>
                    <td className="py-2.5 text-destructive">{st.dropped_count}</td>
                    <td className="py-2.5">
                      {st.drop_off_rate !== null ? `${Math.round(st.drop_off_rate * 100)}%` : "0%"}
                    </td>
                    <td className="py-2.5 font-semibold">
                      {st.median_duration_hours !== null ? `${Math.round(st.median_duration_hours)} hrs` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </Panel>

      {/* Salary Benchmarking Section */}
      <Panel title="2. Market Salary Distributions">
        <div className="p-4">
          <p className="text-xs text-muted-foreground mb-3">
            Percentile compensation estimates segregated by canonical role and currency. A minimum cohort threshold of 5 observations is strictly enforced.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-border text-[11px] uppercase tracking-wider text-muted-foreground font-mono">
                <tr>
                  <th className="pb-2 font-medium">Normalized Role</th>
                  <th className="pb-2 font-medium">Currency / Period</th>
                  <th className="pb-2 font-medium">Sample Size</th>
                  <th className="pb-2 font-medium">P50 Range (Min - Max)</th>
                  <th className="pb-2 font-medium">P25 - P75 Spread</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border text-xs">
                {salaryBenchmarks.map((b) => (
                  <tr key={`${b.role}-${b.currency}`} className="hover:bg-muted/30">
                    <td className="py-2.5 font-medium">{b.role}</td>
                    <td className="py-2.5 font-mono text-muted-foreground">{b.currency} · {b.period}</td>
                    <td className="py-2.5 font-mono">{b.sample_size} jobs</td>
                    <td className="py-2.5 font-mono font-semibold">
                      {b.min_p50 !== null && b.max_p50 !== null
                        ? `${b.currency} ${Math.round(b.min_p50).toLocaleString()} – ${Math.round(b.max_p50).toLocaleString()}`
                        : "Sample too small (<5)"}
                    </td>
                    <td className="py-2.5 font-mono text-muted-foreground">
                      {b.min_p25 !== null && b.max_p75 !== null
                        ? `${Math.round(b.min_p25).toLocaleString()} – ${Math.round(b.max_p75).toLocaleString()}`
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </Panel>

      {/* Skills Gap Roadmap */}
      <Panel title="3. Target Skills Gap & Readiness Roadmap">
        <div className="p-4">
          <p className="text-xs text-muted-foreground mb-3">
            Canonical skills requested in job descriptions that are absent from candidate profile, evaluated through taxonomy normalization.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {skillsGapItems.map((s) => (
              <div
                key={s.skill}
                className={`rounded border p-3 ${s.priority ? "border-amber-500/40 bg-amber-500/5" : "border-border bg-card"}`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-sm">{s.skill}</span>
                  {s.priority && (
                    <span className="rounded bg-amber-500/10 px-1.5 py-0.5 text-[9px] font-bold text-amber-500 uppercase">
                      Priority
                    </span>
                  )}
                </div>
                <div className="mt-2 flex items-baseline justify-between font-mono text-xs text-muted-foreground">
                  <span>Frequency: {s.frequency} jobs</span>
                  <span>{s.percentage}% market demand</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Panel>
    </PageBody>
  );
}
