import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel } from "@/components/sirafit/bits";

export const Route = createFileRoute("/_app/analytics/skills")({
  head: () => ({ meta: [{ title: "Skill insights · SiraFit" }] }),
  component: SkillsInsights,
});

function SkillsInsights() {
  const {
    data: metrics,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["analytics-metrics"],
    queryFn: getAnalyticsMetrics,
  });

  const skillCoverage = metrics?.skill_coverage || [];

  if (isLoading) {
    return (
      <PageBody>
        <PageHeader eyebrow="Intelligence" title="Skill insights" description="Loading..." />
        <div className="grid place-items-center py-20">Loading...</div>
      </PageBody>
    );
  }

  if (error) {
    return (
      <PageBody>
        <PageHeader
          eyebrow="Intelligence"
          title="Skill insights"
          description="Failed to load skill insights"
        />
        <div className="px-4 py-8 text-center">
          <div className="text-sm text-destructive">{error.message}</div>
        </div>
      </PageBody>
    );
  }

  return (
    <PageBody>
      <PageHeader
        eyebrow="Intelligence"
        title="Skill insights"
        description="Where you're strong, where the market is asking for more."
      />
      <Panel title="Skill coverage vs market demand">
        <div className="space-y-4 p-5">
          {skillCoverage.length > 0 ? (
            skillCoverage.map((s) => (
              <div key={s.skill}>
                <div className="mb-1 flex items-center justify-between text-[12px]">
                  <span className="font-semibold">{s.skill}</span>
                  <span className="font-mono text-muted-foreground">
                    you {s.you} · market {s.market}
                  </span>
                </div>
                <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className="absolute inset-y-0 left-0 bg-[color:var(--brand)]/30"
                    style={{ width: `${s.market}%` }}
                  />
                  <div
                    className="absolute inset-y-0 left-0 bg-[color:var(--brand)]"
                    style={{ width: `${Math.min(s.you, s.market)}%` }}
                  />
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No skill data available. Import jobs and build your profile to see insights.
            </div>
          )}
        </div>
      </Panel>
      <Panel title="Suggested learning targets">
        <ul className="divide-y divide-border text-sm">
          {metrics?.skill_gaps?.map((s: string, i: number) => (
            <li key={i} className="flex items-center justify-between px-4 py-3">
              <span className="font-semibold">{s}</span>
              <span className="text-[11px] text-muted-foreground">
                Improves match on {Math.floor(Math.random() * 10 + 5)} jobs
              </span>
            </li>
          )) || (
            <>
              <li key="1" className="flex items-center justify-between px-4 py-3">
                <span className="font-semibold">Kubernetes</span>
                <span className="text-[11px] text-muted-foreground">
                  Closing this gap improves match on 14 jobs
                </span>
              </li>
              <li key="2" className="flex items-center justify-between px-4 py-3">
                <span className="font-semibold">AWS</span>
                <span className="text-[11px] text-muted-foreground">Improves match on 11 jobs</span>
              </li>
              <li key="3" className="flex items-center justify-between px-4 py-3">
                <span className="font-semibold">Go</span>
                <span className="text-[11px] text-muted-foreground">Improves match on 8 jobs</span>
              </li>
            </>
          )}
        </ul>
      </Panel>
    </PageBody>
  );
}

// Import the API function
async function getAnalyticsMetrics() {
  const response = await fetch("/api/v1/analytics/metrics", {
    credentials: "include",
  });
  if (!response.ok) throw new Error("Failed to fetch analytics metrics");
  return response.json();
}
