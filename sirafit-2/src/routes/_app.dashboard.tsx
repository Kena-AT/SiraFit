import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, Stat, ScorePill, StatusPill, AgentDot, Tag } from "@/components/sirafit/bits";
import { applicationsByStatus, eventLog, followUps, getJob, jobs } from "@/lib/mock";

export const Route = createFileRoute("/_app/dashboard")({
  head: () => ({ meta: [{ title: "Dashboard · SiraFit" }] }),
  component: Dashboard,
});

function Dashboard() {
  const top = [...jobs].sort((a, b) => b.match - a.match).slice(0, 5);
  const funnel = Object.entries(applicationsByStatus).map(([k, v]) => ({ k, n: v.length }));
  const maxN = Math.max(1, ...funnel.map((f) => f.n));
  return (
    <PageBody>
      <PageHeader
        eyebrow="System overview"
        title="Command center"
        description="Career telemetry for the last 24 hours. Everything below is live from your local agent."
        actions={
          <>
            <AgentDot label="Gemini connected" />
            <Link to="/jobs/import" className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground hover:bg-foreground/90">Import jobs</Link>
          </>
        }
      />

      <div className="grid gap-3 md:grid-cols-4">
        <Stat label="Pipeline · active" value="14" trend={{ value: "+2 since yesterday", positive: true }} />
        <Stat label="Avg match score" value="84.2%" hint="Deterministic, recomputed hourly" />
        <Stat label="Interview rate" value="8.4%" trend={{ value: "Sector: 3.6%", positive: true }} />
        <Stat label="Local agent uptime" value="99.9%" hint="v0.8.2 · last sync 12s ago" />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="Top match queue" description="Ranked by skill-overlap density" className="lg:col-span-2" actions={<Link to="/jobs" className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground hover:text-foreground">View all →</Link>}>
          <table className="w-full text-left text-sm">
            <tbody className="divide-y divide-border">
              {top.map((j) => (
                <tr key={j.id} className="hover:bg-muted/40">
                  <td className="px-4 py-2.5 font-medium">{j.company}</td>
                  <td className="px-4 py-2.5 text-muted-foreground">{j.role}</td>
                  <td className="px-4 py-2.5"><ScorePill value={j.match} /></td>
                  <td className="px-4 py-2.5 text-right text-[11px] text-muted-foreground tabular-nums">{j.scrapedAt}</td>
                  <td className="px-4 py-2.5 text-right">
                    <Link to="/jobs/$jobId" params={{ jobId: j.id }} className="text-xs font-medium text-[color:var(--brand)] hover:underline">Analyze →</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>

        <Panel title="Application funnel" description="From saved to offer">
          <div className="space-y-2.5 p-4">
            {funnel.map((f) => (
              <div key={f.k} className="flex items-center gap-3">
                <div className="w-24 text-[11px] font-medium text-muted-foreground">{f.k}</div>
                <div className="relative h-5 flex-1 overflow-hidden rounded bg-muted">
                  <div className="absolute inset-y-0 left-0 bg-[color:var(--brand)]/30" style={{ width: `${(f.n / maxN) * 100}%` }} />
                </div>
                <div className="w-8 text-right font-mono text-[11px] font-semibold tabular-nums">{f.n}</div>
              </div>
            ))}
          </div>
        </Panel>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="Pipeline events" description="Append-only event log" className="lg:col-span-2">
          <ul className="divide-y divide-border font-mono text-[11px]">
            {eventLog.map((e, i) => (
              <li key={i} className="flex items-center gap-3 px-4 py-2">
                <span className="text-muted-foreground tabular-nums">{e.t}</span>
                <StatusPill status={e.kind} />
                <span className="text-foreground/80">{e.e}</span>
              </li>
            ))}
          </ul>
        </Panel>

        <Panel title="Upcoming follow-ups" actions={<Link to="/applications/followups" className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground hover:text-foreground">Open →</Link>}>
          <ul className="divide-y divide-border">
            {followUps.slice(0, 4).map((f) => (
              <li key={f.id} className="space-y-1 px-4 py-3">
                <div className="text-[13px] font-medium">{f.what}</div>
                <div className="flex items-center justify-between text-[11px] text-muted-foreground">
                  <span>{f.who}</span>
                  <span className="font-mono tabular-nums">{f.when}</span>
                </div>
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <Panel title="Quick actions">
        <div className="grid gap-px bg-border sm:grid-cols-4">
          {[
            ["Import job", "/jobs/import"],
            ["Tailor resume", "/resumes/builder"],
            ["Draft cover letter", "/cover-letters/builder"],
            ["Run batch analysis", "/batch"],
          ].map(([label, to]) => (
            <Link key={to} to={to} className="bg-card px-4 py-4 text-sm font-medium hover:bg-muted/40">
              <div className="text-foreground">{label} →</div>
              <div className="mt-0.5 text-[11px] text-muted-foreground">Open workflow</div>
            </Link>
          ))}
        </div>
      </Panel>

      <div className="text-[11px] text-muted-foreground">Tracking job <span className="font-mono text-foreground">{getJob("j-001").id}</span> · 12 sources polled · last full sync 12s ago.</div>
    </PageBody>
  );
}