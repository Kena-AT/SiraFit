import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, StatusPill, Tag } from "@/components/sirafit/bits";

export const Route = createFileRoute("/_app/applications/$id")({
  head: () => ({ meta: [{ title: "Application · SiraFit" }] }),
  component: AppDetails,
});

function AppDetails() {
  const { id } = Route.useParams();
  return (
    <PageBody>
      <PageHeader
        eyebrow={`Application · ${id}`}
        title="Linear — Junior Fullstack Developer"
        description="Remote · Applied 4 days ago · Recruiter: Sarah Chen"
        actions={
          <>
            <StatusPill status="Interview" />
            <Link to="/applications" className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted">Back to board</Link>
          </>
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <Panel title="Status history">
            <ul className="divide-y divide-border">
              {[["23 Jun · 09:14","Interview","Recruiter call scheduled for Thu 10:00"],["21 Jun · 11:32","Applied","Resume rv-11 + cover letter cl-03 sent"],["20 Jun · 18:00","Preparing","Tailored resume generated"],["19 Jun · 22:14","Saved","Imported from Ashby"]].map((r) => (
                <li key={r[1] as string + r[0] as string} className="flex items-center gap-4 px-4 py-2.5 text-sm">
                  <span className="w-40 font-mono text-[11px] text-muted-foreground tabular-nums">{r[0]}</span>
                  <StatusPill status={r[1] as string} />
                  <span className="text-foreground/90">{r[2]}</span>
                </li>
              ))}
            </ul>
          </Panel>
          <Panel title="Notes">
            <div className="space-y-3 p-5">
              <div className="rounded bg-muted/40 p-3 text-sm"><div className="font-mono text-[10px] text-muted-foreground">22 Jun</div>Prep call notes — focus on distributed systems internship.</div>
              <textarea className="w-full rounded-md border border-input bg-background p-2 text-sm" rows={3} placeholder="Add a note…" />
            </div>
          </Panel>
          <Panel title="Documents">
            <ul className="divide-y divide-border text-sm">
              <li className="flex items-center justify-between px-4 py-2.5"><span>Resume — rv-11 · Modern template</span><Link to="/resumes/$id" params={{ id: "rv-11" }} className="text-[color:var(--brand)] hover:underline">Preview →</Link></li>
              <li className="flex items-center justify-between px-4 py-2.5"><span>Cover letter — cl-03 · 194 words</span><Link to="/cover-letters" className="text-[color:var(--brand)] hover:underline">Open →</Link></li>
            </ul>
          </Panel>
        </div>
        <div className="space-y-4">
          <Panel title="Recruiter">
            <div className="space-y-2 p-4 text-sm">
              <div className="font-semibold">Sarah Chen</div>
              <div className="text-muted-foreground">Tech recruiter, Linear</div>
              <div className="font-mono text-[11px] text-muted-foreground">sarah@linear.app</div>
            </div>
          </Panel>
          <Panel title="Compensation">
            <div className="space-y-2 p-4 text-sm">
              <div><span className="text-muted-foreground">Posted range:</span> $130k–$165k</div>
              <div><span className="text-muted-foreground">Equity:</span> 0.05% – 0.15%</div>
              <div><span className="text-muted-foreground">Sponsorship:</span> Available</div>
            </div>
          </Panel>
          <Panel title="Tags">
            <div className="flex flex-wrap gap-1.5 p-4">{["TypeScript","React","Trpc","Postgres","Junior friendly"].map((t) => (<Tag key={t}>{t}</Tag>))}</div>
          </Panel>
        </div>
      </div>
    </PageBody>
  );
}