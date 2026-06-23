import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, Tag } from "@/components/sirafit/bits";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { importHistory } from "@/lib/mock";

export const Route = createFileRoute("/_app/jobs/import")({
  head: () => ({ meta: [{ title: "Import jobs · SiraFit" }] }),
  component: Import,
});

function Import() {
  return (
    <PageBody>
      <PageHeader eyebrow="Pipeline" title="Import jobs" description="Paste URLs, paste full descriptions, or upload a batch CSV." actions={<Link to="/jobs/history" className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted">Import history</Link>} />

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="From URL" description="Lever, Greenhouse, Ashby, or generic" className="lg:col-span-1">
          <div className="space-y-3 p-4">
            <Input placeholder="https://jobs.lever.co/company/…" />
            <Button className="w-full">Scrape now</Button>
            <div className="flex flex-wrap gap-1.5 text-[11px] text-muted-foreground">
              Supported: {["Lever","Greenhouse","Ashby","Workday"].map((s) => (<Tag key={s}>{s}</Tag>))}
            </div>
          </div>
        </Panel>
        <Panel title="From description" description="Paste any job description" className="lg:col-span-2">
          <div className="space-y-3 p-4">
            <Textarea rows={8} placeholder="Paste the full job description here…" />
            <div className="flex items-center justify-between">
              <div className="text-[11px] text-muted-foreground">AI will normalize and score this against your master profile.</div>
              <Button>Analyze description</Button>
            </div>
          </div>
        </Panel>
      </div>

      <Panel title="Batch import (CSV)">
        <div className="m-4 grid place-items-center rounded-lg border border-dashed border-border bg-muted/30 px-6 py-12 text-center">
          <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Drop file</div>
          <div className="mt-1 text-sm font-medium">Drop a CSV of URLs or job IDs here</div>
          <div className="mt-1 text-[11px] text-muted-foreground">Max 500 rows per batch · processed locally</div>
          <Button variant="outline" className="mt-3">Choose file</Button>
        </div>
      </Panel>

      <Panel title="Recent imports" actions={<Link to="/jobs/history" className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground hover:text-foreground">View all →</Link>}>
        <ul className="divide-y divide-border text-sm">
          {importHistory.slice(0, 3).map((h) => (
            <li key={h.id} className="flex items-center justify-between px-4 py-2.5">
              <div>
                <div className="font-medium">{h.source}</div>
                <div className="text-[11px] text-muted-foreground">{h.count} jobs · {h.ok} ok · {h.fail} failed</div>
              </div>
              <div className="font-mono text-[11px] text-muted-foreground tabular-nums">{h.when}</div>
            </li>
          ))}
        </ul>
      </Panel>
    </PageBody>
  );
}