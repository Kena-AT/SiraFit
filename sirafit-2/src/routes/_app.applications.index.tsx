import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, ScorePill, StatusPill } from "@/components/sirafit/bits";
import { applicationsByStatus, getJob } from "@/lib/mock";

export const Route = createFileRoute("/_app/applications/")({
  head: () => ({ meta: [{ title: "Applications board · SiraFit" }] }),
  component: Board,
});

function Board() {
  return (
    <PageBody>
      <PageHeader
        eyebrow="Pipeline"
        title="Applications board"
        description="Drag through the hiring lifecycle. Status transitions are deterministic — no AI auto-moves."
        actions={
          <>
            <Link to="/applications/timeline" className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted">Timeline view</Link>
            <Link to="/applications/followups" className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground hover:bg-foreground/90">Follow-ups · 4</Link>
          </>
        }
      />
      <div className="flex gap-4 overflow-x-auto pb-4">
        {Object.entries(applicationsByStatus).map(([col, items]) => (
          <div key={col} className="flex w-72 shrink-0 flex-col gap-2">
            <div className="flex items-center justify-between rounded-md bg-muted/40 px-3 py-1.5">
              <StatusPill status={col} />
              <span className="font-mono text-[11px] font-semibold tabular-nums text-muted-foreground">{items.length}</span>
            </div>
            <div className="flex flex-col gap-2">
              {items.length === 0 ? (
                <div className="grid h-20 place-items-center rounded-md border border-dashed border-border bg-muted/20 font-mono text-[10px] text-muted-foreground">empty</div>
              ) : (
                items.map((it, i) => {
                  const j = getJob(it.jobId);
                  return (
                    <Link key={i} to="/applications/$id" params={{ id: `${it.jobId}-${i}` }} className="space-y-1.5 rounded-md bg-card p-3 ring-1 ring-border hover:ring-[color:var(--brand)]/40">
                      <div className="flex items-center justify-between">
                        <div className="text-[13px] font-semibold">{j.company}</div>
                        <ScorePill value={j.match} />
                      </div>
                      <div className="text-[11px] text-muted-foreground">{j.role}</div>
                      {it.meta ? <div className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium text-foreground/80">{it.meta}</div> : null}
                      <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                        <span>{it.date ?? ""}</span>
                        {it.flag === "warm" ? <span className="text-[color:var(--warning)]">● Warm</span> : null}
                      </div>
                    </Link>
                  );
                })
              )}
            </div>
          </div>
        ))}
      </div>
      <Panel title="Board legend">
        <div className="flex flex-wrap gap-3 px-4 py-3 text-[11px] text-muted-foreground">
          {Object.keys(applicationsByStatus).map((s) => (<StatusPill key={s} status={s} />))}
        </div>
      </Panel>
    </PageBody>
  );
}