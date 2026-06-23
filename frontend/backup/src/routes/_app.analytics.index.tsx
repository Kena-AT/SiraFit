import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, Stat } from "@/components/sirafit/bits";

const funnel = [["Applied", 28],["Recruiter screen", 11],["Tech screen", 6],["Onsite / final", 2],["Offer", 1]] as const;

export const Route = createFileRoute("/_app/analytics/")({
  head: () => ({ meta: [{ title: "Analytics · SiraFit" }] }),
  component: () => (
    <PageBody>
      <PageHeader eyebrow="Intelligence" title="Analytics dashboard" description="Conversion, response time, success metrics. All from your event log." actions={<div className="flex items-center gap-2"><Link to="/analytics/skills" className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted">Skill insights</Link><Link to="/analytics/market" className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted">Market insights</Link></div>} />
      <div className="grid gap-3 md:grid-cols-4">
        <Stat label="Applications" value="28" trend={{ value: "+4 this week", positive: true }} />
        <Stat label="Interview rate" value="21.4%" hint="6 of 28" />
        <Stat label="Avg response time" value="3.2d" />
        <Stat label="Offer rate" value="3.6%" hint="1 of 28" />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Conversion funnel">
          <div className="space-y-2.5 p-4">
            {funnel.map(([k, n]) => (
              <div key={k} className="flex items-center gap-3">
                <div className="w-36 text-[12px]">{k}</div>
                <div className="relative h-6 flex-1 overflow-hidden rounded bg-muted"><div className="absolute inset-y-0 left-0 bg-[color:var(--brand)]/40" style={{ width: `${(n / 28) * 100}%` }} /></div>
                <div className="w-8 text-right font-mono text-[11px] font-semibold tabular-nums">{n}</div>
              </div>
            ))}
          </div>
        </Panel>
        <Panel title="Rejection stages">
          <ul className="divide-y divide-border text-sm">
            {[["Resume screen", 14],["Recruiter call", 4],["Tech screen", 3],["Onsite", 1]].map((r) => (
              <li key={r[0] as string} className="flex items-center justify-between px-4 py-2.5"><span>{r[0]}</span><span className="font-mono tabular-nums">{r[1]}</span></li>
            ))}
          </ul>
        </Panel>
      </div>
    </PageBody>
  ),
});