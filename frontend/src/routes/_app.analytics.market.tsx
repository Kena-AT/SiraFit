import { createFileRoute } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel } from "@/components/sirafit/bits";

export const Route = createFileRoute("/_app/analytics/market")({
  head: () => ({ meta: [{ title: "Market insights · SiraFit" }] }),
  component: () => (
    <PageBody>
      <PageHeader eyebrow="Intelligence" title="Job market insights" description="Demand and trends across the roles SiraFit watches." />
      <Panel title="Roles by demand">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-border bg-muted/40 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            <tr><th className="px-4 py-2.5">Role</th><th className="px-4 py-2.5">Demand</th><th className="px-4 py-2.5">Postings (30d)</th><th className="px-4 py-2.5">Trend</th></tr>
          </thead>
          <tbody className="divide-y divide-border">
            {marketRoles.map((r) => (
              <tr key={r.role} className="hover:bg-muted/30">
                <td className="px-4 py-3 font-medium">{r.role}</td>
                <td className="px-4 py-3"><div className="h-1.5 w-32 overflow-hidden rounded-full bg-muted"><div className="h-full bg-[color:var(--brand)]" style={{ width: `${r.demand}%` }} /></div></td>
                <td className="px-4 py-3 font-mono tabular-nums">{r.postings.toLocaleString()}</td>
                <td className={`px-4 py-3 font-mono ${r.change.startsWith("-") ? "text-destructive" : "text-[color:var(--success)]"}`}>{r.change}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Top technologies (in postings)">
          <ul className="divide-y divide-border text-sm">{[["TypeScript", 71],["Python", 64],["React", 58],["AWS", 56],["Kubernetes", 41]].map((r) => (<li key={r[0] as string} className="flex items-center justify-between px-4 py-2.5"><span>{r[0]}</span><span className="font-mono text-muted-foreground tabular-nums">{r[1]}%</span></li>))}</ul>
        </Panel>
        <Panel title="Salary medians (Junior)">
          <ul className="divide-y divide-border text-sm">{[["SF Bay Area","$165k"],["NYC","$155k"],["Remote (US)","$145k"],["Berlin","€68k"],["London","£72k"]].map((r) => (<li key={r[0]} className="flex items-center justify-between px-4 py-2.5"><span>{r[0]}</span><span className="font-mono tabular-nums">{r[1]}</span></li>))}</ul>
        </Panel>
      </div>
    </PageBody>
  ),
});