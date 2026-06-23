import { createFileRoute } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel } from "@/components/sirafit/bits";
import { skillMatrix } from "@/lib/mock";

export const Route = createFileRoute("/_app/analytics/skills")({
  head: () => ({ meta: [{ title: "Skill insights · SiraFit" }] }),
  component: () => (
    <PageBody>
      <PageHeader eyebrow="Intelligence" title="Skill insights" description="Where you're strong, where the market is asking for more." />
      <Panel title="Skill coverage vs market demand">
        <div className="space-y-4 p-5">
          {skillMatrix.map((s) => (
            <div key={s.skill}>
              <div className="mb-1 flex items-center justify-between text-[12px]">
                <span className="font-semibold">{s.skill}</span>
                <span className="font-mono text-muted-foreground">you {s.you} · market {s.market}</span>
              </div>
              <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-muted">
                <div className="absolute inset-y-0 left-0 bg-[color:var(--brand)]/30" style={{ width: `${s.market}%` }} />
                <div className="absolute inset-y-0 left-0 bg-[color:var(--brand)]" style={{ width: `${Math.min(s.you, s.market)}%` }} />
              </div>
            </div>
          ))}
        </div>
      </Panel>
      <Panel title="Suggested learning targets">
        <ul className="divide-y divide-border text-sm">
          {[["Kubernetes","Closing this gap improves match on 14 jobs"],["AWS","Improves match on 11 jobs"],["Go","Improves match on 8 jobs"]].map((r) => (
            <li key={r[0]} className="flex items-center justify-between px-4 py-3"><span className="font-semibold">{r[0]}</span><span className="text-[11px] text-muted-foreground">{r[1]}</span></li>
          ))}
        </ul>
      </Panel>
    </PageBody>
  ),
});