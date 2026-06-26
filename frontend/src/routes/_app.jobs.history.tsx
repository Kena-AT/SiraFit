import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, StatusPill, EmptyState } from "@/components/sirafit/bits";
import { getImportHistory } from "@/lib/api/jobs";
import { Button } from "@/components/ui/button";
import type { JobImportRecord } from "@/types/job";

export const Route = createFileRoute("/_app/jobs/history")({
  head: () => ({ meta: [{ title: "Import history · SiraFit" }] }),
  component: History,
});

function formatDate(dateStr: string) {
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  } catch {
    return dateStr;
  }
}

function History() {
  const [history, setHistory] = useState<JobImportRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = () => {
    setLoading(true);
    setError(null);
    getImportHistory(0, 50)
      .then(setHistory)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  return (
    <PageBody>
      <PageHeader
        eyebrow="Pipeline"
        title="Import history"
        description="Every import run, success or fail. Reprocess any failed batch."
        actions={
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={fetchHistory} disabled={loading}>
              {loading ? "Refreshing..." : "Refresh"}
            </Button>
            <Link to="/jobs/import" className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground hover:bg-foreground/90">
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
            <Button variant="outline" size="sm" className="mt-3" onClick={fetchHistory}>Retry</Button>
          </div>
        ) : history.length === 0 ? (
          <EmptyState
            title="No imports yet"
            body="Import jobs from URLs or paste descriptions to build your history."
            action={<Link to="/jobs/import" className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground">Import jobs</Link>}
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
                  <td className="px-4 py-3 text-right tabular-nums text-[color:var(--success)]">{h.ok_count}</td>
                  <td className="px-4 py-3 text-right tabular-nums text-destructive">{h.fail_count}</td>
                  <td className="px-4 py-3 font-mono text-[11px] text-muted-foreground tabular-nums">{formatDate(h.created_at)}</td>
                  <td className="px-4 py-3"><StatusPill status={h.status} /></td>
                  <td className="px-4 py-3 text-right">
                    {h.status === "failed" ? (
                      <Button variant="outline" size="sm">Reprocess</Button>
                    ) : h.fail_count > 0 ? (
                      <Button variant="outline" size="sm">Review</Button>
                    ) : (
                      <span className="text-[11px] text-muted-foreground">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Panel>
    </PageBody>
  );
}
