import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, Stat } from "@/components/sirafit/bits";
import { getAnalyticsMetrics } from "@/lib/api/notifications";

export const Route = createFileRoute("/_app/analytics/")({
  head: () => ({ meta: [{ title: "Analytics · SiraFit" }] }),
  component: AnalyticsDashboard,
});

function AnalyticsDashboard() {
  const {
    data: metrics,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["analytics-metrics"],
    queryFn: getAnalyticsMetrics,
  });

  if (isLoading) {
    return (
      <PageBody>
        <PageHeader eyebrow="Intelligence" title="Analytics dashboard" description="Loading..." />
        <div className="grid place-items-center py-20">Loading...</div>
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
  const maxFunnel = Math.max(...funnel.map(([, n]) => n), 1);
  const rejectionStages = metrics?.rejection_stages || [];

  return (
    <PageBody>
      <PageHeader
        eyebrow="Intelligence"
        title="Analytics dashboard"
        description="Conversion, response time, success metrics. All from your event log."
        actions={
          <div className="flex items-center gap-2">
            <Link
              to="/analytics/skills"
              className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted"
            >
              Skill insights
            </Link>
            <Link
              to="/analytics/market"
              className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted"
            >
              Market insights
            </Link>
          </div>
        }
      />
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
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Conversion funnel">
          <div className="space-y-2.5 p-4">
            {funnel.map(([k, n]) => (
              <div key={k} className="flex items-center gap-3">
                <div className="w-36 text-[12px]">{k}</div>
                <div className="relative h-6 flex-1 overflow-hidden rounded bg-muted">
                  <div
                    className="absolute inset-y-0 left-0 bg-[color:var(--brand)]/40"
                    style={{ width: `${(n / maxFunnel) * 100}%` }}
                  />
                </div>
                <div className="w-8 text-right font-mono text-[11px] font-semibold tabular-nums">
                  {n}
                </div>
              </div>
            ))}
          </div>
        </Panel>
        <Panel title="Rejection stages">
          <ul className="divide-y divide-border text-sm">
            {rejectionStages.map((r) => (
              <li key={r[0] as string} className="flex items-center justify-between px-4 py-2.5">
                <span>{r[0]}</span>
                <span className="font-mono tabular-nums">{r[1]}</span>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </PageBody>
  );
}
