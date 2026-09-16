import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, StatusPill, EmptyState } from "@/components/sirafit/bits";
import { getImportHistory, getImportDetail, deleteImport } from "@/lib/api/jobs";
import { Button } from "@/components/ui/button";
import { JobNavTabs } from "@/components/sirafit/job-nav-tabs";
import { ConfirmDialog } from "@/components/sirafit/confirm-dialog";
import { toast } from "sonner";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import type { JobImportRecord, ImportResult } from "@/types/job";

export const Route = createFileRoute("/_app/jobs/history")({
  head: () => ({ meta: [{ title: "Import history · SiraFit" }] }),
  component: History,
});

function formatDate(dateStr: string) {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

function History() {
  const [history, setHistory] = useState<JobImportRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedImport, setSelectedImport] = useState<ImportResult | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);

  const fetchHistory = () => {
    setLoading(true);
    setError(null);
    getImportHistory(0, 50)
      .then(setHistory)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  const handleReview = async (importId: string) => {
    setDetailLoading(true);
    setSelectedImport(null);
    setDialogOpen(true);
    try {
      const detail = await getImportDetail(importId);
      setSelectedImport(detail);
    } catch (e: any) {
      setError(e.message);
      setDialogOpen(false);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleDelete = (importId: string) => {
    setConfirmDialogOpen(true);
    setPendingDeleteId(importId);
  };

  const confirmDelete = async () => {
    const importId = pendingDeleteId;
    setConfirmDialogOpen(false);
    setPendingDeleteId(null);
    if (!importId) return;
    try {
      await deleteImport(importId);
      toast.success("Import deleted");
      setHistory((prev) => prev.filter((h) => h.id !== importId));
      if (selectedImport?.import_record.id === importId) {
        setSelectedImport(null);
        setDialogOpen(false);
      }
    } catch (e: any) {
      toast.error(e.message || "Failed to delete import");
      setError(e.message);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  return (
    <PageBody>
      <JobNavTabs />
      <PageHeader
        eyebrow="Pipeline"
        title="Import history"
        description="Every import run, success or fail. Reprocess any failed batch."
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={fetchHistory} disabled={loading}>
              {loading ? "Refreshing..." : "Refresh"}
            </Button>
            <Link
              to="/jobs/import"
              className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground hover:bg-foreground/90"
            >
              New import
            </Link>
          </div>
        }
      />
      <Panel>
        {loading ? (
          <div className="flex items-center justify-center px-4 py-12 text-sm text-muted-foreground">
            <span className="inline-block mr-2 h-4 w-4 animate-spin rounded-full border-2 border-border border-t-foreground" />
            Loading history...
          </div>
        ) : error ? (
          <div className="px-4 py-8 text-center">
            <div className="text-sm text-destructive">{error}</div>
            <Button variant="outline" size="sm" className="mt-3" onClick={fetchHistory}>
              Retry
            </Button>
          </div>
        ) : history.length === 0 ? (
          <EmptyState
            title="No imports yet"
            body="Import jobs from URLs or paste descriptions to build your history."
            action={
              <Link
                to="/jobs/import"
                className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground"
              >
                Import jobs
              </Link>
            }
          />
        ) : (
          <table className="w-full text-left text-sm">
            <thead className="border-b border-border bg-muted/40 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              <tr>
                <th className="px-4 py-2.5 font-semibold">Source</th>
                <th className="px-4 py-2.5 font-semibold text-right">Found</th>
                <th className="px-4 py-2.5 font-semibold text-right">OK</th>
                <th className="px-4 py-2.5 font-semibold text-right">Fail</th>
                <th className="px-4 py-2.5 font-semibold">Date</th>
                <th className="px-4 py-2.5 font-semibold">Status</th>
                <th className="px-4 py-2.5 text-right font-semibold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {history.map((h) => (
                <tr key={h.id} className="hover:bg-muted/30">
                  <td className="px-4 py-3 font-medium capitalize">{h.source}</td>
                  <td className="px-4 py-3 text-right tabular-nums">{h.total_found}</td>
                  <td className="px-4 py-3 text-right tabular-nums text-[color:var(--success)]">
                    {h.ok_count}
                  </td>
                  <td className="px-4 py-3 text-right tabular-nums text-destructive">
                    {h.fail_count}
                  </td>
                  <td className="px-4 py-3 font-mono text-[11px] text-muted-foreground tabular-nums">
                    {formatDate(h.created_at)}
                  </td>
                  <td className="px-4 py-3">
                    <StatusPill status={h.status} />
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-1.5">
                      {h.status === "completed" || h.status === "failed" ? (
                        <Button variant="outline" size="sm" onClick={() => handleReview(h.id)}>
                          Review
                        </Button>
                      ) : null}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive/70 hover:text-destructive"
                        onClick={() => handleDelete(h.id)}
                      >
                        Delete
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>

      {/* Review modal */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Import detail</DialogTitle>
            <DialogDescription>
              {selectedImport
                ? `${selectedImport.import_record.source} import · ${formatDate(selectedImport.import_record.created_at)}`
                : "Loading import details..."}
            </DialogDescription>
          </DialogHeader>

          {detailLoading && (
            <div className="flex items-center justify-center py-10 text-sm text-muted-foreground">
              <span className="inline-block mr-2 h-4 w-4 animate-spin rounded-full border-2 border-border border-t-foreground" />
              Loading...
            </div>
          )}

          {selectedImport && !detailLoading && (
            <div className="space-y-4">
              {/* Summary row */}
              <div className="flex flex-wrap gap-4 text-xs items-center">
                <span className="rounded bg-muted px-2 py-1 font-medium capitalize">
                  {selectedImport.import_record.source}
                </span>
                <span>
                  Status: <StatusPill status={selectedImport.import_record.status} />
                </span>
                <span>
                  Found:{" "}
                  <span className="font-semibold">{selectedImport.import_record.total_found}</span>
                </span>
                <span>
                  Imported:{" "}
                  <span className="font-semibold text-emerald-600">
                    {selectedImport.import_record.ok_count}
                  </span>
                </span>
                <span>
                  Failed:{" "}
                  <span className="font-semibold text-destructive">
                    {selectedImport.import_record.fail_count}
                  </span>
                </span>
                {selectedImport.import_record.partial && (
                  <span className="rounded bg-amber-500/10 px-2 py-1 text-[10px] font-semibold uppercase text-amber-600">
                    Partial
                  </span>
                )}
                {selectedImport.scrape_method && (
                  <span
                    className={
                      selectedImport.scrape_method === "scrapling"
                        ? "rounded bg-emerald-500/10 px-2 py-1 text-[10px] font-semibold uppercase text-emerald-600"
                        : "rounded bg-amber-500/10 px-2 py-1 text-[10px] font-semibold uppercase text-amber-600"
                    }
                  >
                    {selectedImport.scrape_method === "scrapling" ? "Smart Parsed" : "Heuristic"}
                  </span>
                )}
                {selectedImport.source_platform && (
                  <span className="rounded bg-muted px-2 py-1 text-[10px] font-medium">
                    {selectedImport.source_platform}
                  </span>
                )}
                {selectedImport.scrape_duration_ms != null && (
                  <span className="text-muted-foreground">
                    {selectedImport.scrape_duration_ms}ms
                  </span>
                )}
              </div>

              {/* Errors */}
              {selectedImport.errors.length > 0 && (
                <div className="rounded-md border border-destructive/20 bg-destructive/5 p-3">
                  <div className="mb-1 text-xs font-semibold uppercase text-destructive">
                    Errors
                  </div>
                  {selectedImport.errors.map((err, i) => (
                    <div key={i} className="text-xs text-destructive/80">
                      {err}
                    </div>
                  ))}
                </div>
              )}

              {/* Jobs list */}
              {selectedImport.jobs.length > 0 ? (
                <div className="divide-y divide-border rounded-md border border-border">
                  {selectedImport.jobs.map((job, i) => (
                    <div key={i} className="flex items-start justify-between gap-4 px-4 py-3">
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
                            <span className="text-sm font-semibold">{job.title}</span>
                          )}
                          {job.status === "imported" && (
                            <span className="rounded bg-emerald-500/10 px-1.5 py-0.5 text-[10px] font-medium text-emerald-600">
                              Imported
                            </span>
                          )}
                          {job.status === "duplicate" && (
                            <span className="rounded bg-amber-500/10 px-1.5 py-0.5 text-[10px] font-medium text-amber-600">
                              Duplicate
                            </span>
                          )}
                          {job.status === "failed" && (
                            <span className="rounded bg-destructive/10 px-1.5 py-0.5 text-[10px] font-medium text-destructive">
                              Failed
                            </span>
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          {job.company}
                          {job.location ? ` · ${job.location}` : ""}
                        </div>
                        {job.error && (
                          <div className="mt-1 text-xs text-destructive font-mono">{job.error}</div>
                        )}
                        {job.tags && job.tags.length > 0 && (
                          <div className="mt-1 flex flex-wrap gap-1">
                            {job.tags.map((t) => (
                              <span
                                key={t}
                                className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium"
                              >
                                {t}
                              </span>
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
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="py-6 text-center text-sm text-muted-foreground">
                  No jobs in this import batch.
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation */}
      <ConfirmDialog
        open={confirmDialogOpen}
        title="Delete import?"
        description="This will permanently delete this import record. Jobs created during this import will remain in your system."
        onConfirm={confirmDelete}
        onCancel={() => setConfirmDialogOpen(false)}
      />
    </PageBody>
  );
}
