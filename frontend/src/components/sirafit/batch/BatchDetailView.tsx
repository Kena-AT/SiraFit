"use client";

import { useEffect } from "react";
import { RefreshCw, RotateCcw, XCircle } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageHeader, Panel, StatusPill, ScoreMeter } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { getBatchJob, retryBatchJob, cancelBatchJob } from "@/lib/api/batch";
import type { BatchJob } from "@/lib/api/batch";
import { BatchItemRow } from "./BatchItemRow";

interface BatchDetailViewProps {
  batchJob: BatchJob;
  onRefetch: () => void;
}

export function BatchDetailView({ batchJob, onRefetch }: BatchDetailViewProps) {
  const queryClient = useQueryClient();
  const isRunning = ["pending", "running"].includes(batchJob.status);

  // Poll while running
  const { data: liveJob, refetch } = useQuery({
    queryKey: ["batch-job", batchJob.id],
    queryFn: () => getBatchJob(batchJob.id),
    enabled: isRunning,
    refetchInterval: isRunning ? 2000 : false,
  });

  // Update parent when done
  useEffect(() => {
    if (liveJob && !isRunning) {
      onRefetch();
    }
  }, [liveJob, isRunning, onRefetch]);

  const displayJob = liveJob || batchJob;
  const progressPct =
    displayJob.total_items > 0
      ? Math.round((displayJob.processed_items / displayJob.total_items) * 100)
      : 0;

  const retryMutation = useMutation({
    mutationFn: retryBatchJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["batch-job", batchJob.id] });
      queryClient.invalidateQueries({ queryKey: ["batch-jobs"] });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: cancelBatchJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["batch-job", batchJob.id] });
      queryClient.invalidateQueries({ queryKey: ["batch-jobs"] });
    },
  });

  return (
    <div>
      <PageHeader
        eyebrow="Operations"
        title={`${displayJob.operation_type.charAt(0).toUpperCase() + displayJob.operation_type.slice(1)} batch`}
        description={`${displayJob.processed_items} / ${displayJob.total_items} items processed`}
        actions={
          <div className="flex items-center gap-2">
            {isRunning && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => refetch()}
                disabled={cancelMutation.isPending}
              >
                <RefreshCw className="w-4 h-4 mr-1 animate-spin" /> Refresh
              </Button>
            )}
            {["pending", "running"].includes(displayJob.status) && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => cancelMutation.mutate(displayJob.id)}
                disabled={cancelMutation.isPending}
              >
                <XCircle className="w-4 h-4 mr-1" /> Cancel
              </Button>
            )}
            {["completed", "failed", "partial", "cancelled"].includes(displayJob.status) &&
              displayJob.failed_items > 0 && (
                <Button
                  size="sm"
                  onClick={() => retryMutation.mutate(displayJob.id)}
                  disabled={retryMutation.isPending}
                >
                  <RotateCcw className="w-4 h-4 mr-1" /> Retry failed ({displayJob.failed_items})
                </Button>
              )}
          </div>
        }
      />

      <Panel title="Progress">
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="h-3 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full bg-[color:var(--brand)] transition-all duration-300"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
            </div>
            <div className="flex items-center gap-4 text-sm font-mono tabular-nums">
              <span className="text-[color:var(--success)]">✓ {displayJob.succeeded_items}</span>
              <span className="text-destructive">✗ {displayJob.failed_items}</span>
              <span className="text-muted-foreground">
                ⟳ {displayJob.total_items - displayJob.processed_items}
              </span>
            </div>
          </div>
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Started:</span>{" "}
              {displayJob.started_at ? new Date(displayJob.started_at).toLocaleString() : "—"}
            </div>
            <div>
              <span className="text-muted-foreground">Completed:</span>{" "}
              {displayJob.completed_at ? new Date(displayJob.completed_at).toLocaleString() : "—"}
            </div>
            <div>
              <span className="text-muted-foreground">Status:</span>{" "}
              <StatusPill status={displayJob.status} />
            </div>
            <div>
              <span className="text-muted-foreground">Cancel requested:</span>{" "}
              {String(displayJob.cancel_requested)}
            </div>
          </div>
        </div>
      </Panel>

      <Panel title="Items">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-muted-foreground">
                <th className="px-4 py-2 font-mono text-[10px] uppercase">Job ID</th>
                <th className="px-4 py-2 font-mono text-[10px] uppercase">Status</th>
                <th className="px-4 py-2 font-mono text-[10px] uppercase">Details</th>
                <th className="px-4 py-2 font-mono text-[10px] uppercase text-right">Error</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {Object.entries(displayJob.result_summary).map(([itemId, result]) => (
                <BatchItemRow key={itemId} itemId={itemId} result={result} />
              ))}
            </tbody>
          </table>
          {Object.keys(displayJob.result_summary).length === 0 && (
            <div className="p-8 text-center text-muted-foreground">No items processed yet</div>
          )}
        </div>
      </Panel>

      <Panel title="Payload">
        <pre className="p-4 text-[11px] font-mono bg-muted/50 rounded overflow-auto max-h-64">
          {JSON.stringify(displayJob.payload, null, 2)}
        </pre>
      </Panel>
    </div>
  );
}
