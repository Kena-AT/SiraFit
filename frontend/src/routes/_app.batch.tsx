import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader } from "@/components/sirafit/bits";
import { BatchJobList } from "@/components/sirafit/batch/BatchJobList";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { getBatchJob, type BatchJob } from "@/lib/api/batch";

export const Route = createFileRoute("/_app/batch")({
  component: BatchJobsPage,
});

function BatchJobsPage() {
  const [selectedJob, setSelectedJob] = useState<BatchJob | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);

  const handleViewDetails = async (jobId: string) => {
    setDialogOpen(true);
    setLoadingDetails(true);
    try {
      const job = await getBatchJob(jobId);
      setSelectedJob(job);
    } catch (err) {
      console.error("Failed to load batch job details:", err);
    } finally {
      setLoadingDetails(false);
    }
  };

  return (
    <PageBody>
      <PageHeader
        eyebrow="Batch Processing"
        title="Batch Jobs"
        description="View and manage your batch operations."
        actions={
          <Link to="/jobs">
            <Button variant="outline">Back to Jobs</Button>
          </Link>
        }
      />
      <BatchJobList onViewDetails={handleViewDetails} />

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="capitalize">
              {selectedJob?.operation_type || "Batch"} Job Details
            </DialogTitle>
            <DialogDescription className="font-mono text-xs">
              ID: {selectedJob?.id}
            </DialogDescription>
          </DialogHeader>

          {loadingDetails ? (
            <div className="py-8 text-center text-sm text-muted-foreground">Loading details...</div>
          ) : selectedJob ? (
            <div className="space-y-4 text-sm">
              <div className="grid grid-cols-2 gap-3 rounded-lg border border-border p-3 text-xs sm:grid-cols-4">
                <div>
                  <span className="text-muted-foreground">Status</span>
                  <div className="font-semibold capitalize text-foreground">
                    {selectedJob.status}
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground">Total Items</span>
                  <div className="font-semibold text-foreground">{selectedJob.total_items}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">Succeeded</span>
                  <div className="font-semibold text-emerald-600">
                    {selectedJob.succeeded_items}
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground">Failed</span>
                  <div className="font-semibold text-destructive">{selectedJob.failed_items}</div>
                </div>
              </div>

              {selectedJob.payload && (
                <div>
                  <div className="font-semibold text-xs uppercase tracking-wider text-muted-foreground mb-1">
                    Payload Parameters
                  </div>
                  <pre className="overflow-x-auto rounded bg-muted/40 p-3 text-xs font-mono">
                    {JSON.stringify(selectedJob.payload, null, 2)}
                  </pre>
                </div>
              )}

              {selectedJob.result_summary && Object.keys(selectedJob.result_summary).length > 0 && (
                <div>
                  <div className="font-semibold text-xs uppercase tracking-wider text-muted-foreground mb-1">
                    Result Summary ({Object.keys(selectedJob.result_summary).length} items)
                  </div>
                  <div className="max-h-60 space-y-2 overflow-y-auto rounded border border-border p-2">
                    {Object.entries(selectedJob.result_summary).map(([itemId, res]) => (
                      <div
                        key={itemId}
                        className="flex flex-col gap-1 rounded bg-muted/30 p-2 text-xs font-mono"
                      >
                        <div className="flex items-center justify-between">
                          <span className="truncate max-w-xs">{itemId}</span>
                          <span
                            className={
                              res.status === "success" ? "text-emerald-600" : "text-destructive"
                            }
                          >
                            {res.status}
                          </span>
                        </div>
                        {res.error && (
                          <div className="text-destructive text-[11px]">{res.error}</div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="py-4 text-sm text-destructive">Failed to load details.</div>
          )}
        </DialogContent>
      </Dialog>
    </PageBody>
  );
}
