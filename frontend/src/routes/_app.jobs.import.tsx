import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, Tag, StatusPill, EmptyState } from "@/components/sirafit/bits";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { importJobs, getImportHistory } from "@/lib/api/jobs";
import type { ImportResult, JobData, JobImportRecord } from "@/types/job";

export const Route = createFileRoute("/_app/jobs/import")({
  head: () => ({ meta: [{ title: "Import jobs · SiraFit" }] }),
  component: Import,
});

function ImportPreview({ jobs, errors }: { jobs: JobData[]; errors: string[] }) {
  if (jobs.length === 0 && errors.length === 0) return null;

  return (
    <Panel title="Import results">
      <div className="divide-y divide-border">
        {errors.length > 0 && (
          <div className="px-4 py-3">
            <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-destructive">Errors</div>
            {errors.map((err, i) => (
              <div key={i} className="text-sm text-destructive/80">{err}</div>
            ))}
          </div>
        )}
        {jobs.map((job, i) => (
          <div key={i} className="px-4 py-3">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-semibold">{job.title}</h3>
                  {job.is_duplicate && <Tag>duplicate</Tag>}
                </div>
                <p className="text-sm text-muted-foreground">{job.company}</p>
                {job.location && <p className="text-xs text-muted-foreground">{job.location}</p>}
                {job.tags.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {job.tags.map((t) => (<Tag key={t}>{t}</Tag>))}
                  </div>
                )}
              </div>
              <div className="shrink-0 text-right">
                {(job.salary_min || job.salary_max) && (
                  <div className="text-sm tabular-nums">
                    {job.salary_min ? `$${job.salary_min.toLocaleString()}` : ""}
                    {job.salary_min && job.salary_max ? " – " : ""}
                    {job.salary_max ? `$${job.salary_max.toLocaleString()}` : ""}
                  </div>
                )}
                <StatusPill status={job.source} />
              </div>
            </div>
            {job.description && (
              <p className="mt-2 line-clamp-3 text-xs text-muted-foreground">{job.description}</p>
            )}
          </div>
        ))}
      </div>
    </Panel>
  );
}

function Import() {
  const [url, setUrl] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [recentHistory, setRecentHistory] = useState<JobImportRecord[]>([]);

  const handleImportUrl = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await importJobs({ source_type: 'url', data: url });
      setResult(res);
      getImportHistory(0, 3).then(setRecentHistory).catch(() => {});
    } catch (e: any) {
      setResult({ import_record: null as any, jobs: [], errors: [e.message] });
    } finally {
      setLoading(false);
    }
  };

  const handleImportDescription = async () => {
    if (!description.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await importJobs({ source_type: 'description', data: description });
      setResult(res);
      getImportHistory(0, 3).then(setRecentHistory).catch(() => {});
    } catch (e: any) {
      setResult({ import_record: null as any, jobs: [], errors: [e.message] });
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageBody>
      <PageHeader
        eyebrow="Pipeline"
        title="Import jobs"
        description="Paste URLs, paste full descriptions, or upload a batch CSV."
        actions={
          <Link to="/jobs/history" className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted">
            Import history
          </Link>
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel title="From URL" description="Lever, Greenhouse, Ashby, or generic" className="lg:col-span-1">
          <div className="space-y-3 p-4">
            <Input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://jobs.lever.co/company/…" />
            <Button className="w-full" onClick={handleImportUrl} disabled={loading || !url.trim()}>
              {loading ? "Importing..." : "Scrape now"}
            </Button>
            <div className="flex flex-wrap gap-1.5 text-[11px] text-muted-foreground">
              Supported: {["LinkedIn", "Indeed", "Glassdoor", "Greenhouse"].map((s) => (<Tag key={s}>{s}</Tag>))}
            </div>
          </div>
        </Panel>
        <Panel title="From description" description="Paste any job description" className="lg:col-span-2">
          <div className="space-y-3 p-4">
            <Textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={8} placeholder="Paste the full job description here…" />
            <div className="flex items-center justify-between">
              <div className="text-[11px] text-muted-foreground">AI will normalize and score this against your master profile.</div>
              <Button onClick={handleImportDescription} disabled={loading || !description.trim()}>
                {loading ? "Analyzing..." : "Analyze description"}
              </Button>
            </div>
          </div>
        </Panel>
      </div>

      {loading && (
        <Panel title="Processing">
          <div className="flex items-center justify-center gap-2 px-4 py-8 text-sm text-muted-foreground">
            <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-border border-t-foreground" />
            Importing job data...
          </div>
        </Panel>
      )}

      {result && !loading && (
        <>
          {result.import_record && (
            <Panel title="Import summary">
              <div className="flex flex-wrap gap-6 px-4 py-3">
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Status</div>
                  <StatusPill status={result.import_record.status} />
                </div>
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Found</div>
                  <div className="mt-0.5 font-mono text-lg font-semibold tabular-nums">{result.import_record.total_found}</div>
                </div>
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Imported</div>
                  <div className="mt-0.5 font-mono text-lg font-semibold tabular-nums text-[color:var(--success)]">{result.import_record.ok_count}</div>
                </div>
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Failed</div>
                  <div className="mt-0.5 font-mono text-lg font-semibold tabular-nums text-destructive">{result.import_record.fail_count}</div>
                </div>
              </div>
            </Panel>
          )}
          <ImportPreview jobs={result.jobs} errors={result.errors} />
        </>
      )}

      <Panel title="Batch import (CSV)">
        <div className="m-4 grid place-items-center rounded-lg border border-dashed border-border bg-muted/30 px-6 py-12 text-center">
          <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">Drop file</div>
          <div className="mt-1 text-sm font-medium">Drop a CSV of URLs or job IDs here</div>
          <div className="mt-1 text-[11px] text-muted-foreground">Max 500 rows per batch · processed locally</div>
          <Button variant="outline" className="mt-3">Choose file</Button>
        </div>
      </Panel>

      <Panel title="Recent imports" actions={<Link to="/jobs/history" className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground hover:text-foreground">View all →</Link>}>
        {recentHistory.length > 0 ? (
          <ul className="divide-y divide-border text-sm">
            {recentHistory.map((h) => (
              <li key={h.id} className="flex items-center justify-between px-4 py-2.5">
                <div>
                  <div className="font-medium">{h.source === 'url' ? 'URL import' : h.source === 'description' ? 'Description import' : h.source}</div>
                  <div className="text-[11px] text-muted-foreground">{h.total_found} jobs · {h.ok_count} ok · {h.fail_count} failed</div>
                </div>
                <div className="flex items-center gap-3">
                  <StatusPill status={h.status} />
                  <div className="font-mono text-[11px] text-muted-foreground tabular-nums">{new Date(h.created_at).toLocaleDateString()}</div>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState title="No imports yet" body="Import a job from a URL or description to see it here." />
        )}
      </Panel>
    </PageBody>
  );
}
