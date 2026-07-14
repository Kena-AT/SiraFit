import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel } from "@/components/sirafit/bits";

interface MarketRole {
  role: string;
  demand: number;
  postings: number;
  change: string;
}

interface TechStat {
  0: string;
  1: number;
}

interface SalaryStat {
  0: string;
  1: string;
}

export const Route = createFileRoute("/_app/analytics/market")({
  head: () => ({ meta: [{ title: "Market insights · SiraFit" }] }),
  component: MarketInsights,
});

function MarketInsights() {
  const {
    data: metrics,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["analytics-metrics"],
    queryFn: getAnalyticsMetrics,
  });

  const marketRoles = (metrics?.market_demand as MarketRole[]) || [];
  const topTechs = (metrics?.top_technologies as TechStat[]) || [
    ["TypeScript", 71],
    ["Python", 64],
    ["React", 58],
    ["AWS", 56],
    ["Kubernetes", 41],
  ];
  const salaryMedians = (metrics?.salary_medians as SalaryStat[]) || [
    ["SF Bay Area", "$165k"],
    ["NYC", "$155k"],
    ["Remote (US)", "$145k"],
    ["Berlin", "€68k"],
    ["London", "£72k"],
  ];

  if (isLoading) {
    return (
      <PageBody>
        <PageHeader eyebrow="Intelligence" title="Job market insights" description="Loading..." />
        <div className="grid place-items-center py-20">Loading...</div>
      </PageBody>
    );
  }

  if (error) {
    return (
      <PageBody>
        <PageHeader
          eyebrow="Intelligence"
          title="Job market insights"
          description="Failed to load market insights"
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
        title="Job market insights"
        description="Demand and trends across the roles SiraFit watches."
      />
      <Panel title="Roles by demand">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-border bg-muted/40 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            <tr>
              <th className="px-4 py-2.5">Role</th>
              <th className="px-4 py-2.5">Demand</th>
              <th className="px-4 py-2.5">Postings (30d)</th>
              <th className="px-4 py-2.5">Trend</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {marketRoles.map((r: MarketRole) => (
              <tr key={r.role} className="hover:bg-muted/30">
                <td className="px-4 py-3 font-medium">{r.role}</td>
                <td className="px-4 py-3">
                  <div className="h-1.5 w-32 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full bg-[color:var(--brand)]"
                      style={{ width: `${r.demand}%` }}
                    />
                  </div>
                </td>
                <td className="px-4 py-3 font-mono tabular-nums">{r.postings.toLocaleString()}</td>
                <td
                  className={`px-4 py-3 font-mono ${r.change.startsWith("-") ? "text-destructive" : "text-[color:var(--success)]"}`}
                >
                  {r.change}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Top technologies (in postings)">
          <ul className="divide-y divide-border text-sm">
            {topTechs.map((r: TechStat) => (
              <li key={r[0]} className="flex items-center justify-between px-4 py-2.5">
                <span>{r[0]}</span>
                <span className="font-mono text-muted-foreground tabular-nums">{r[1]}%</span>
              </li>
            ))}
          </ul>
        </Panel>
        <Panel title="Salary medians (Junior)">
          <ul className="divide-y divide-border text-sm">
            {salaryMedians.map((r: SalaryStat) => (
              <li key={r[0]} className="flex items-center justify-between px-4 py-2.5">
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

async function getAnalyticsMetrics() {
  const response = await fetch("/api/v1/analytics/metrics", {
    credentials: "include",
  });
  if (!response.ok) throw new Error("Failed to fetch analytics metrics");
  return response.json();
}
