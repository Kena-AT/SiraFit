import { createFileRoute } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, StatusPill } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";

const ops = [
  { id: "b-204", op: "Bulk analyze", scope: "54 jobs · Greenhouse", progress: 100, status: "completed" },
  { id: "b-203", op: "Bulk score", scope: "All saved (28)", progress: 100, status: "completed" },
  { id: "b-202", op: "Bulk tag · 'remote'", scope: "12 jobs", progress: 75, status: "info" },
  { id: "b-201", op: "Bulk archive · rejected > 30d", scope: "9 applications", progress: 0, status: "warning" },
];

export const Route = createFileRoute("/_app/batch")({
  head: () => ({ meta: [{ title: "Batch processing · SiraFit" }] }),
  component: () => (
    <PageBody>
      <PageHeader eyebrow="Operations" title="Batch processing center" description="Run high-volume operations across your pipeline. Bounded retries, no infinite loops." actions={<Button>+ New batch job</Button>} />
      <div className="grid gap-3 md:grid-cols-4">
        {[["Bulk analyze","Score every imported job"],["Bulk tag","Apply filters at scale"],["Bulk archive","Clean out the dead"],["Bulk re-score","After profile change"]].map(([t, d]) => (
          <button key={t} className="rounded-lg bg-card p-4 text-left ring-1 ring-border hover:ring-[color:var(--brand)]/40">
            <div className="text-sm font-semibold">{t}</div>
            <div className="mt-1 text-[11px] text-muted-foreground">{d}</div>
          </button>
        ))}
      </div>
      <Panel title="Recent batches">
        <ul className="divide-y divide-border">
          {ops.map((o) => (
            <li key={o.id} className="flex items-center gap-4 px-4 py-3">
              <span className="w-16 font-mono text-[11px] text-muted-foreground">{o.id}</span>
              <div className="flex-1">
                <div className="text-sm font-semibold">{o.op}</div>
                <div className="text-[11px] text-muted-foreground">{o.scope}</div>
              </div>
              <div className="w-40">
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted"><div className="h-full bg-[color:var(--brand)]" style={{ width: `${o.progress}%` }} /></div>
              </div>
              <StatusPill status={o.status} />
            </li>
          ))}
        </ul>
      </Panel>
    </PageBody>
  ),
});