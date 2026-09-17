import { useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, Stat } from "@/components/sirafit/bits";
import {
  getAnalyticsMetrics,
  downloadAnalyticsExport,
  type SalaryBenchmark,
  type SkillGapItem,
  type StageInsight,
} from "@/lib/api/analytics";

export const Route = createFileRoute("/_app/analytics/")({
  head: () => ({ meta: [{ title: "Analytics · SiraFit" }] }),
  component: AnalyticsDashboard,
});

function AnalyticsDashboard() {
  const [isExporting, setIsExporting] = useState(false);

  const {
    data: metrics,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["analytics-metrics"],
    queryFn: getAnalyticsMetrics,
    staleTime: 60000, // 60 seconds to match backend cache TTL
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

  if (isLoading) {
    return (
      <PageBody>
        <PageHeader eyebrow="Intelligence" title="Analytics dashboard" description="Loading..." />
        <div className="grid place-items-center py-20 text-muted-foreground">Loading analytics...</div>
      </PageBody>
    );
  }

  if (error) {
    return (
      <PageBody>
        <PageHeader
          eyebrow="Intelligence"
          title="Analytics dashboard"
          description="Failed to load metrics"
        />
        <div className="px-4 py-8 text-center">
          <div className="text-sm text-destructive">{error.message}</div>
        </div>
      </PageBody>
    );
  }

  const funnel = metrics?.conversion_funnel || [];
  const maxFunnel = Math.max(...funnel.map((f: { count: number }) => f.count), 1);
  const rejectionStages = metrics?.rejection_stages || [];
  const salaryBenchmarks: SalaryBenchmark[] = metrics?.salary_benchmarks || [];
  const skillsGapItems: SkillGapItem[] = metrics?.skills_gap_analysis?.skills || [];
  const stallStages: StageInsight[] = metrics?.stall_insights?.stages || [];

  return (
    <PageBody>
      <PageHeader
        eyebrow="Intelligence"
        title="Analytics dashboard"
        description="Conversion, response time, salary benchmarks, and stage stall insights."
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={handleExport}
              disabled={isExporting}
              className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted disabled:opacity-50 transition-colors"
            >
              {isExporting ? "Exporting..." : "Export Excel"}
            </button>
            <Link
              to="/analytics/report"
              className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted transition-colors"
            >
              Full report
            </Link>
            <Link
              to="/analytics/skills"
              className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted transition-colors"
            >
              Skill insights
            </Link>
            <Link
              to="/analytics/market"
              className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted transition-colors"
            >
              Market insights
            </Link>
          </div>
        }
      />

      {/* Top Level Metric KPIs */}
      <div className="grid gap-3 md:grid-cols-4">
        <Stat
          label="Applications"
          value={metrics?.total_applications?.toString() || "0"}
          trend={{ value: "+0 this week", positive: true }}
        />
        <Stat
          label="Interview rate"
          value={`${metrics?.interview_rate?.toFixed(1) || "0"}%`}
          hint={`${Math.round(((metrics?.interview_rate || 0) * (metrics?.total_applications || 0)) / 100)} of ${metrics?.total_applications || 0}`}
        />
        <Stat
          label="Avg response time"
          value={`${metrics?.avg_response_time_days?.toFixed(1) || "0"}d`}
        />
        <Stat
          label="Offer rate"
          value={`${metrics?.offer_rate?.toFixed(1) || "0"}%`}
          hint={`${Math.round(((metrics?.offer_rate || 0) * (metrics?.total_applications || 0)) / 100)} of ${metrics?.total_applications || 0}`}
        />
      </div>

      {/* Sprint 10: Salary Benchmarks Section */}
      <Panel title="Market Salary Benchmarks">
        <div className="p-4">
          <div className="mb-3 text-[11px] text-muted-foreground">
            P50 posted minimum to P50 posted maximum from comparable jobs with verified salary metadata (min 5 samples required for percentiles).
          </div>
          {salaryBenchmarks.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-border text-[11px] uppercase tracking-wider text-muted-foreground font-mono">
                  <tr>
                    <th className="pb-2 font-medium">Role</th>
                    <th className="pb-2 font-medium">Currency</th>
                    <th className="pb-2 font-medium">Sample Size</th>
                    <th className="pb-2 font-medium">P50 Range (Min – Max)</th>
                    <th className="pb-2 font-medium">P25 – P75 Spread</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {salaryBenchmarks.map((b) => (
                    <tr key={`${b.role}-${b.currency}-${b.period}`} className="hover:bg-muted/30">
                      <td className="py-2.5 font-medium">{b.role}</td>
                      <td className="py-2.5 font-mono text-xs text-muted-foreground">{b.currency} ({b.period})</td>
                      <td className="py-2.5 font-mono text-xs">{b.sample_size} jobs</td>
                      <td className="py-2.5 font-mono font-semibold text-xs">
                        {b.min_p50 !== null && b.max_p50 !== null
                          ? `${b.currency} ${Math.round(b.min_p50).toLocaleString()} – ${Math.round(b.max_p50).toLocaleString()}`
                          : b.sample_size < 5
                            ? <span className="text-muted-foreground font-normal italic">Insufficient sample (need 5+)</span>
                            : "N/A"}
                      </td>
                      <td className="py-2.5 font-mono text-xs text-muted-foreground">
                        {b.min_p25 !== null && b.max_p75 !== null
                          ? `${Math.round(b.min_p25).toLocaleString()} – ${Math.round(b.max_p75).toLocaleString()}`
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-6 text-center text-xs text-muted-foreground">
              No salary metadata available across imported jobs yet.
            </div>
          )}
        </div>
      </Panel>

      {/* Skills Gap & Stall Insights Grid */}
      <div className="grid gap-4 lg:grid-cols-2">
        {/* Sprint 10: Canonical Skills Gap */}
        <Panel title="Priority Skills Gap Analysis">
          <div className="p-4">
            <div className="mb-3 text-[11px] text-muted-foreground">
              Missing skills from candidate profile with highest demand across analyzed job postings.
            </div>
            {skillsGapItems.length > 0 ? (
              <div className="space-y-3">
                {skillsGapItems.slice(0, 8).map((s) => (
                  <div key={s.skill} className="flex items-center gap-3">
                    <div className="w-28 text-[12px] font-medium truncate">{s.skill}</div>
                    <div className="relative h-4 flex-1 overflow-hidden rounded bg-muted">
                      <div
                        className={`absolute inset-y-0 left-0 ${s.priority ? "bg-amber-500/70" : "bg-[color:var(--brand)]/50"}`}
                        style={{ width: `${Math.min(s.percentage, 100)}%` }}
                      />
                    </div>
                    <div className="w-12 text-right font-mono text-[11px] font-semibold tabular-nums">
                      {s.percentage}%
                    </div>
                    {s.priority && (
                      <span className="rounded bg-amber-500/10 px-1.5 py-0.5 text-[9px] font-bold text-amber-500 uppercase tracking-wide">
                        Priority
                      </span>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-6 text-center text-xs text-muted-foreground">
                No skills gap detected. All required skills match candidate profile.
              </div>
            )}
          </div>
        </Panel>

        {/* Sprint 10: Application Stall & Drop-off Insights */}
        <Panel title="Application Stall & Stage Dwell">
          <div className="p-4">
            <div className="mb-3 text-[11px] text-muted-foreground">
              Stage duration and stage-specific drop-off rates from confirmed timeline events.
            </div>
            {stallStages.length > 0 ? (
              <div className="space-y-2.5">
                {stallStages.map((st) => (
                  <div key={st.stage} className="flex items-center justify-between border-b border-border/50 pb-2 text-xs">
                    <div>
                      <span className="font-medium capitalize">{st.stage.replace("_", " ")}</span>
                      <span className="ml-2 font-mono text-[10px] text-muted-foreground">
                        {st.entered_count} entered · {st.progressed_count} progressed
                      </span>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="font-mono text-[11px]">
                        {st.drop_off_rate !== null
                          ? <span className={st.drop_off_rate > 0.4 ? "text-destructive font-semibold" : "text-muted-foreground"}>
                              {Math.round(st.drop_off_rate * 100)}% drop
                            </span>
                          : "0% drop"}
                      </div>
                      <div className="w-20 text-right font-mono text-[11px] font-medium text-foreground">
                        {st.median_duration_hours !== null
                          ? `${Math.round(st.median_duration_hours)}h median`
                          : <span className="text-muted-foreground font-normal text-[10px]">(&lt;3 events)</span>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-6 text-center text-xs text-muted-foreground">
                No stage transitions recorded yet.
              </div>
            )}
          </div>
        </Panel>
      </div>

      {/* Legacy Funnel and Rejection Stages Grid */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Conversion Funnel">
          <div className="space-y-2.5 p-4">
            {funnel.map((f: { stage: string; count: number }) => (
              <div key={f.stage} className="flex items-center gap-3">
                <div className="w-36 text-[12px]">{f.stage}</div>
                <div className="relative h-6 flex-1 overflow-hidden rounded bg-muted">
                  <div
                    className="absolute inset-y-0 left-0 bg-[color:var(--brand)]/40"
                    style={{ width: `${(f.count / maxFunnel) * 100}%` }}
                  />
                </div>
                <div className="w-8 text-right font-mono text-[11px] font-semibold tabular-nums">
                  {f.count}
                </div>
              </div>
            ))}
          </div>
        </Panel>
        <Panel title="Rejection Stages">
          <ul className="divide-y divide-border text-sm">
            {rejectionStages.map((r: { stage: string; count: number }) => (
              <li key={r.stage} className="flex items-center justify-between px-4 py-2.5">
                <span>{r.stage}</span>
                <span className="font-mono tabular-nums">{r.count}</span>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </PageBody>
  );
}
