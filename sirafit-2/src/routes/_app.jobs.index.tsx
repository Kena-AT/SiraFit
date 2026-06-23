import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, ScoreMeter, StatusPill, Tag } from "@/components/sirafit/bits";
import { jobs } from "@/lib/mock";
import { Input } from "@/components/ui/input";

export const Route = createFileRoute("/_app/jobs/")({
  head: () => ({ meta: [{ title: "Jobs Explorer · SiraFit" }] }),
  component: JobsExplorer,
});

function JobsExplorer() {
  return (
    <PageBody>
      <PageHeader
        eyebrow="Pipeline"
        title="Jobs Explorer"
        description="842 jobs ingested from 12 ATS sources. Filter, score, and triage."
        actions={
          <>
            <Link to="/jobs/history" className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted">Import history</Link>
            <Link to="/jobs/import" className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground hover:bg-foreground/90">Import jobs</Link>
          </>
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative max-w-xs flex-1">
          <Input placeholder="Search role, company, skill…" className="h-9 bg-card" />
        </div>
        {["Match > 80", "Remote", "Source: Lever", "Posted < 24h", "+ Add filter"].map((f) => (
          <span key={f} className="rounded-md bg-card px-2.5 py-1 text-xs font-medium ring-1 ring-border">{f}</span>
        ))}
        <div className="ml-auto font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">{jobs.length} loaded</div>
      </div>

      <Panel>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border bg-muted/40 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              <tr>
                <th className="px-4 py-2.5 font-semibold">#</th>
                <th className="px-4 py-2.5 font-semibold">Company</th>
                <th className="px-4 py-2.5 font-semibold">Role</th>
                <th className="px-4 py-2.5 font-semibold">Match</th>
                <th className="px-4 py-2.5 font-semibold">Salary</th>
                <th className="px-4 py-2.5 font-semibold">Source</th>
                <th className="px-4 py-2.5 font-semibold">Tags</th>
                <th className="px-4 py-2.5 font-semibold">Scraped</th>
                <th className="px-4 py-2.5 text-right font-semibold">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {jobs.map((j, i) => (
                <tr key={j.id} className="group hover:bg-muted/30">
                  <td className="px-4 py-3 font-mono text-[11px] text-muted-foreground tabular-nums">{String(i + 1).padStart(3, "0")}</td>
                  <td className="px-4 py-3 font-medium">{j.company}</td>
                  <td className="px-4 py-3 text-muted-foreground"><Link to="/jobs/$jobId" params={{ jobId: j.id }} className="hover:text-foreground hover:underline">{j.role}</Link></td>
                  <td className="px-4 py-3"><ScoreMeter value={j.match} /></td>
                  <td className="px-4 py-3 text-muted-foreground tabular-nums">{j.salary}</td>
                  <td className="px-4 py-3 text-muted-foreground"><Tag>{j.source}</Tag></td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {j.tags.slice(0, 3).map((t) => (<Tag key={t}>{t}</Tag>))}
                    </div>
                  </td>
                  <td className="px-4 py-3 font-mono text-[11px] text-muted-foreground tabular-nums">{j.scrapedAt}</td>
                  <td className="px-4 py-3 text-right">{j.status ? <StatusPill status={j.status} /> : <span className="text-[10px] text-muted-foreground">—</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <footer className="flex items-center justify-between border-t border-border bg-muted/30 px-4 py-2 text-[11px] text-muted-foreground">
          <div>Showing 1–{jobs.length} of 842</div>
          <div className="flex gap-1.5">
            <button className="rounded border border-border bg-card px-2 py-0.5 hover:bg-muted">←</button>
            <button className="rounded border border-border bg-card px-2 py-0.5 hover:bg-muted">→</button>
          </div>
        </footer>
      </Panel>
    </PageBody>
  );
}