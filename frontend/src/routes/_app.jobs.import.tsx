import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useRef, useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, Tag, StatusPill, EmptyState } from "@/components/sirafit/bits";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { importJobs, getImportHistory } from "@/lib/api/jobs";
import { JobNavTabs } from "@/components/sirafit/job-nav-tabs";
import { ImportProgressCard } from "@/components/sirafit/jobs/ImportProgressCard";
import { SessionImportModal } from "@/components/sirafit/jobs/SessionImportModal";
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
            <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-destructive">
              Errors
            </div>
            {errors.map((err, i) => (
              <div key={i} className="text-sm text-destructive/80">
                {err}
              </div>
            ))}
          </div>
        )}
        {jobs.map((job, i) => (
          <div key={i} className="px-4 py-3">
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  {job.id ? (
                    <Link
                      to="/jobs/$jobId"
                      params={{ jobId: job.id }}
                      className="text-sm font-semibold hover:underline text-foreground"
                    >
                      {job.title}
                    </Link>
                  ) : (
                    <h3 className="text-sm font-semibold">{job.title}</h3>
                  )}
                  {job.is_duplicate && <Tag>duplicate</Tag>}
                </div>
                <p className="text-sm text-muted-foreground">{job.company}</p>
                {job.location && <p className="text-xs text-muted-foreground">{job.location}</p>}
                {job.tags && job.tags.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {job.tags.map((t) => (
                      <Tag key={t}>{t}</Tag>
                    ))}
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
  const queryClient = useQueryClient();
  const [url, setUrl] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeImportId, setActiveImportId] = useState<string | null>(null);
  const [sessionModalOpen, setSessionModalOpen] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [recentHistory, setRecentHistory] = useState<JobImportRecord[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFileName, setSelectedFileName] = useState("");

  const handleImportCompleted = useCallback(
    (detail: ImportResult) => {
      setActiveImportId(null);
      setResult(detail);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      queryClient.invalidateQueries({ queryKey: ["ranked-jobs"] });
      getImportHistory(0, 3)
        .then(setRecentHistory)
        .catch(() => {});
    },
    [queryClient],
  );

  const handleImportError = useCallback(() => {
    setActiveImportId(null);
  }, []);

  const handleFile = async (file: File) => {
    setSelectedFileName(file.name);
    setLoading(true);
    setResult(null);
    try {
      const text = await file.text();
      const res = await importJobs({ source_type: "csv", data: text });
      setResult(res);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      queryClient.invalidateQueries({ queryKey: ["ranked-jobs"] });
      try {
        const history = await getImportHistory(0, 3);
        setRecentHistory(history);
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        console.error("Failed to fetch import history:", msg);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setResult({
        import_record: null as unknown as import("@/types/job").JobImportRecord,
        jobs: [],
        errors: [msg],
      });
    } finally {
      setLoading(false);
    }
  };

  const handleImportUrl = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await importJobs({ source_type: "url", data: url });
      if (res.import_record?.status === "processing" || res.scrape_method === "async") {
        setActiveImportId(res.import_record.id);
      } else {
        setResult(res);
      }
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      queryClient.invalidateQueries({ queryKey: ["ranked-jobs"] });
      try {
        const history = await getImportHistory(0, 3);
        setRecentHistory(history);
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        console.error("Failed to fetch import history:", msg);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setResult({
        import_record: null as unknown as import("@/types/job").JobImportRecord,
        jobs: [],
        errors: [msg],
      });
    } finally {
      setLoading(false);
    }
  };

  const handleImportDescription = async () => {
    if (!description.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await importJobs({ source_type: "description", data: description });
      setResult(res);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
      queryClient.invalidateQueries({ queryKey: ["ranked-jobs"] });
      try {
        const history = await getImportHistory(0, 3);
        setRecentHistory(history);
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : String(e);
        console.error("Failed to fetch import history:", msg);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setResult({
        import_record: null as unknown as import("@/types/job").JobImportRecord,
        jobs: [],
        errors: [msg],
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageBody>
      <JobNavTabs />
      <PageHeader
        eyebrow="Pipeline"
        title="Import jobs"
        description="Paste URLs, paste full descriptions, or upload a batch CSV."
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => setSessionModalOpen(true)}>
              Saved-jobs session
            </Button>
            <Link
              to="/jobs/history"
              className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted"
            >
              Import history
            </Link>
          </div>
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <Panel
          title="From URL"
          description="Lever, Greenhouse, Ashby, or generic"
          className="lg:col-span-1"
        >
          <div className="space-y-3 p-4">
            <Input
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://jobs.lever.co/company/…"
            />
            <Button className="w-full" onClick={handleImportUrl} disabled={loading || !url.trim()}>
              {loading ? "Importing..." : "Scrape now"}
            </Button>
            <div className="flex flex-wrap gap-1.5 text-[11px] text-muted-foreground">
              Supported:{" "}
              {[
                "LinkedIn",
                "Indeed",
                "Glassdoor",
                "Greenhouse",
                "Lever",
                "Ashby",
                "ZipRecruiter",
              ].map((s) => (
                <Tag key={s}>{s}</Tag>
              ))}
            </div>
          </div>
        </Panel>
        <Panel
          title="From description"
          description="Paste any job description"
          className="lg:col-span-2"
        >
          <div className="space-y-3 p-4">
            <Textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={8}
              placeholder="Paste the full job description here…"
            />
            <div className="flex items-center justify-between">
              <div className="text-[11px] text-muted-foreground">
                AI will normalize and score this against your master profile.
              </div>
              <Button onClick={handleImportDescription} disabled={loading || !description.trim()}>
                {loading ? "Analyzing..." : "Analyze description"}
              </Button>
            </div>
          </div>
        </Panel>
      </div>

      {activeImportId && (
        <ImportProgressCard
          importId={activeImportId}
          sourceType="URL"
          onCompleted={handleImportCompleted}
          onError={handleImportError}
        />
      )}

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
              <div className="flex flex-wrap gap-6 px-4 py-3 items-center">
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                    Status
                  </div>
                  <StatusPill status={result.import_record.status} />
                </div>
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                    Found
                  </div>
                  <div className="mt-0.5 font-mono text-lg font-semibold tabular-nums">
                    {result.import_record.total_found}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                    Imported
                  </div>
                  <div className="mt-0.5 font-mono text-lg font-semibold tabular-nums text-success">
                    {result.import_record.ok_count}
                  </div>
                </div>
                <div>
                  <div className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                    Failed
                  </div>
                  <div className="mt-0.5 font-mono text-lg font-semibold tabular-nums text-destructive">
                    {result.import_record.fail_count}
                  </div>
                </div>
                {result.import_record.partial && (
                  <div>
                    <div className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                      Quality
                    </div>
                    <span className="mt-1 inline-block rounded bg-amber-500/10 px-2 py-0.5 text-xs font-semibold text-amber-600">
                      Partial
                    </span>
                  </div>
                )}
              </div>
            </Panel>
          )}

          {/* Scrape metadata badge — shown only for URL imports */}
          {result.scrape_method && (
            <div className="flex items-center gap-2 rounded-md border border-border bg-card px-4 py-2 text-xs text-muted-foreground">
              <span
                className={
                  result.scrape_method === "scrapling"
                    ? "inline-block rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase text-emerald-600"
                    : "inline-block rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] font-semibold uppercase text-amber-600"
                }
              >
                {result.scrape_method === "scrapling" ? "Smart Parsed" : "Heuristic"}
              </span>
              {result.source_platform && (
                <span className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium">
                  {result.source_platform}
                </span>
              )}
              {result.scrape_duration_ms != null && <span>{result.scrape_duration_ms}ms</span>}
              {result.fields_extracted != null && result.fields_extracted > 0 && (
                <span>{result.fields_extracted} fields extracted</span>
              )}
            </div>
          )}
          <ImportPreview jobs={result.jobs} errors={result.errors} />
        </>
      )}

      <Panel title="Batch import (CSV)">
        <div
          className="m-4 grid place-items-center rounded-lg border border-dashed border-border bg-muted/30 px-6 py-12 text-center cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
              handleFile(e.dataTransfer.files[0]);
            }
          }}
        >
          <input
            type="file"
            accept=".csv,.txt"
            ref={fileInputRef}
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                handleFile(e.target.files[0]);
              }
            }}
          />
          <div className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
            {loading ? "Importing batch..." : "Drop file"}
          </div>
          <div className="mt-1 text-sm font-medium">
            {selectedFileName
              ? `Selected: ${selectedFileName}`
              : "Drop a CSV of URLs or job IDs here"}
          </div>
          <div className="mt-1 text-[11px] text-muted-foreground">
            Max 500 rows per batch · processed locally
          </div>
          <Button variant="outline" className="mt-3 pointer-events-none">
            {loading ? "Processing..." : "Choose file"}
          </Button>
        </div>
      </Panel>

      <Panel
        title="Saved jobs session import"
        description="Discover and import your saved jobs from LinkedIn or Indeed"
      >
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4">
          <div className="space-y-1">
            <p className="text-sm font-medium text-foreground">Authenticated session scraping</p>
            <p className="text-xs text-muted-foreground">
              Provide your session cookie to securely discover and queue your saved jobs
              asynchronously.
            </p>
            <div className="flex gap-1.5 pt-1">
              <Tag>LinkedIn</Tag>
              <Tag>Indeed</Tag>
            </div>
          </div>
          <Button onClick={() => setSessionModalOpen(true)} className="shrink-0">
            Import saved jobs
          </Button>
        </div>
      </Panel>

      <Panel
        title="Recent imports"
        actions={
          <Link
            to="/jobs/history"
            className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground hover:text-foreground"
          >
            View all →
          </Link>
        }
      >
        {recentHistory.length > 0 ? (
          <ul className="divide-y divide-border text-sm">
            {recentHistory.map((h) => (
              <li key={h.id} className="flex items-center justify-between px-4 py-2.5">
                <div>
                  <div className="font-medium">
                    {h.source === "url"
                      ? "URL import"
                      : h.source === "description"
                        ? "Description import"
                        : h.source}
                  </div>
                  <div className="text-[11px] text-muted-foreground">
                    {h.total_found} jobs · {h.ok_count} ok · {h.fail_count} failed
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <StatusPill status={h.status} />
                  <div className="font-mono text-[11px] text-muted-foreground tabular-nums">
                    {new Date(h.created_at).toLocaleDateString()}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <EmptyState
            title="No imports yet"
            body="Import a job from a URL or description to see it here."
          />
        )}
      </Panel>

      <SessionImportModal
        isOpen={sessionModalOpen}
        onClose={() => setSessionModalOpen(false)}
        onImportStarted={(id) => {
          setActiveImportId(id);
          queryClient.invalidateQueries({ queryKey: ["jobs"] });
          queryClient.invalidateQueries({ queryKey: ["ranked-jobs"] });
        }}
      />
    </PageBody>
  );
}
