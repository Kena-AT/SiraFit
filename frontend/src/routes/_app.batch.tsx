import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, StatusPill, EmptyState } from "@/components/sirafit/bits";
import { Plus, RefreshCw } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { getBatchJobs, createBatchJob, cancelBatchJob, type BatchJobCreateInput, type BatchOperationType } from "@/lib/api/batch";
import { getJobs } from "@/lib/api/jobs";
import { BatchCreateModal } from "@/components/sirafit/batch/BatchCreateModal";
import { useState } from "react";

export const Route = createFileRoute("/_app/batch")({
  head: () => ({ meta: [{ title: "Batch processing · SiraFit" }] }),
  component: BatchCenter,
});

function BatchCenter() {
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>("all");
  const [filterOp, setFilterOp] = useState<string>("all");

  const { data: jobs = [] } = useQuery({ queryKey: ["jobs-for-batch"], queryFn: () => getJobs({ limit: 500 }) });
  const { data: batchData, isLoading } = useQuery({
    queryKey: ["batch-jobs", filterStatus === "all" ? undefined : filterStatus, filterOp === "all" ? undefined : filterOp],
    queryFn: () => getBatchJobs({
      status: filterStatus === "all" ? undefined : filterStatus,
      operation_type: filterOp === "all" ? undefined : filterOp,
    }),
  });

  const batchJobs = batchData?.jobs ?? [];

  const createMutation = useMutation({
    mutationFn: createBatchJob,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["batch-jobs"] });
      setModalOpen(false);
    },
  });

  const cancelMutation = useMutation({
    mutationFn: cancelBatchJob,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["batch-jobs"] }),
  });

  const handleCreate = (input: { operation_type: BatchOperationType; job_ids: string[]; params?: Record<string, unknown> }) => {
    createMutation.mutate(input);
  };

  if (isLoading) {
    return (
      <PageBody>
        <PageHeader eyebrow="Operations" title="Batch processing center" />
        <div className="grid place-items-center py-20">Loading...</div>
      </PageBody>
    );
  }

  return (
    <PageBody>
      <PageHeader
        eyebrow="Operations"
        title="Batch processing center"
        description="Run high-volume operations across your pipeline. Bounded retries, no infinite loops."
        actions={
          <Button onClick={() => setModalOpen(true)}>
            <Plus className="w-4 h-4 mr-2" /> New batch job
          </Button>
        }
      />
      <div className="space-y-4">
        <Panel title="Create batch job" className="border-border/50">
          <BatchCreateModal
            isOpen={modalOpen}
            onClose={() => setModalOpen(false)}
            onSubmit={handleCreate}
            availableJobs={jobs}
          />
          <Button variant="outline" onClick={() => setModalOpen(true)} className="w-full">
            <Plus className="w-4 h-4 mr-2" /> Start new batch operation
          </Button>
        </Panel>

        <Panel title="Recent batches">
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <Input placeholder="Filter batches..." className="w-64" />
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="running">Running</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="partial">Partial</SelectItem>
                <SelectItem value="failed">Failed</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterOp} onValueChange={setFilterOp}>
              <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All operations</SelectItem>
                <SelectItem value="analyze">Analyze</SelectItem>
                <SelectItem value="score">Score</SelectItem>
                <SelectItem value="tag">Tag</SelectItem>
                <SelectItem value="archive">Archive</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex flex-col gap-3">
            {batchJobs.length === 0 ? (
              <EmptyState
                title="No batch jobs yet"
                body="Create a batch job to process multiple items at once."
                action={
                  <Button onClick={() => setModalOpen(true)} className="w-full">
                    <Plus className="w-4 h-4 mr-2" /> Create batch job
                  </Button>
                }
              />
            ) : (
              batchJobs.map((batchJob) => (
                <div
                  key={batchJob.id}
                  className="flex items-center gap-4 p-4 rounded-lg bg-card ring-1 ring-border hover:ring-[color:var(--brand)]/40 transition-colors cursor-pointer"
                  onClick={() => window.location.href = `/batch/${batchJob.id}`}
                >
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <StatusPill status={batchJob.operation_type} className="shrink-0" />
                    <div className="min-w-0">
                      <div className="text-sm font-semibold truncate">
                        {batchJob.operation_type.charAt(0).toUpperCase() + batchJob.operation_type.slice(1)}
                      </div>
                      <div className="text-[11px] text-muted-foreground">
                        {batchJob.processed_items} / {batchJob.total_items} items
                      </div>
                    </div>
                  </div>
                  <div className="w-32 shrink-0">
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                      <div
                        className="h-full bg-[color:var(--brand)]"
                        style={{ width: `${batchJob.total_items > 0
                          ? Math.round((batchJob.processed_items / batchJob.total_items) * 100)
                          : 0}%` }}
                      />
                    </div>
                  </div>
                  <StatusPill status={batchJob.status} className="shrink-0" />
                </div>
              ))
            )}
          </div>
        </Panel>
      </div>
    </PageBody>
  );
}