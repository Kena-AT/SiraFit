import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, ScoreMeter, Tag } from "@/components/sirafit/bits";

export const Route = createFileRoute("/_app/match")({
  head: () => ({ meta: [{ title: "Match analysis · SiraFit" }] }),
  component: () => {
    const top = [...jobs].sort((a, b) => b.match - a.match).slice(0, 8);
    return (
      <PageBody>
        <PageHeader eyebrow="Intelligence" title="Match analysis" description="Deterministic fit between your master profile and every job in pipeline." />
        <div className="grid gap-4 lg:grid-cols-3">
          <Panel title="Skill gap" className="lg:col-span-1">
            <ul className="divide-y divide-border text-sm">
              {[["gRPC","3 jobs missing"],["Terraform","5 jobs missing"],["Rust","2 jobs missing"],["Vitess","1 job missing"]].map((r) => (
                <li key={r[0]} className="flex items-center justify-between px-4 py-2.5"><span>{r[0]}</span><span className="text-[11px] text-muted-foreground">{r[1]}</span></li>
              ))}
            </ul>
          </Panel>
          <Panel title="Top matches with explanations" className="lg:col-span-2">
            <ul className="divide-y divide-border">
              {top.map((j) => (
                <li key={j.id} className="space-y-2 px-4 py-3">
                  <div className="flex items-center justify-between">
                    <Link to="/jobs/$jobId" params={{ jobId: j.id }} className="text-sm font-semibold hover:underline">{j.company} — {j.role}</Link>
                    <ScoreMeter value={j.match} />
                  </div>
                  <div className="text-[12px] text-muted-foreground">Strong alignment on {j.tags.slice(0, 2).join(" + ")}. Gap on {j.tags.slice(2, 3).join(", ") || "domain experience"}.</div>
                  <div className="flex flex-wrap gap-1.5">{j.tags.map((t) => (<Tag key={t}>{t}</Tag>))}</div>
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      </PageBody>
    );
  },
});