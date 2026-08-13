import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, ScorePill, StatusPill, EmptyState } from "@/components/sirafit/bits";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getApplications,
  transitionApplicationStatus,
  createApplication,
  getFollowUps,
} from "@/lib/api/applications";
import { getJobs } from "@/lib/api/jobs";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { toast } from "sonner";

// Status columns for the Kanban board
const STATUS_COLUMNS = [
  "saved",
  "preparing",
  "applied",
  "screening",
  "interview",
  "final_round",
  "offer",
  "rejected",
  "withdrawn",
  "archived",
];

export const Route = createFileRoute("/_app/applications/")({
  head: () => ({ meta: [{ title: "Applications board · SiraFit" }] }),
  component: Board,
});

function Board() {
  const queryClient = useQueryClient();
  const [addOpen, setAddOpen] = useState(false);
  const [selectedJobId, setSelectedJobId] = useState<string>("");

  const { data: applications = [], isLoading } = useQuery({
    queryKey: ["applications"],
    queryFn: getApplications,
  });

  // Live follow-up count — only upcoming (not past)
  const { data: followups = [] } = useQuery({
    queryKey: ["followups", false],
    queryFn: () => getFollowUps(false),
  });

  // Jobs for "add application" dialog
  const { data: jobsData, isLoading: jobsLoading } = useQuery({
    queryKey: ["jobs-for-add-app"],
    queryFn: () => getJobs({ limit: 200 }),
    enabled: addOpen,
  });
  const jobs = jobsData?.jobs ?? [];

  const transitionMutation = useMutation({
    mutationFn: ({ id, toStatus }: { id: string; toStatus: string }) =>
      transitionApplicationStatus(id, toStatus),
    // Optimistic update: move card immediately
    onMutate: async ({ id, toStatus }) => {
      await queryClient.cancelQueries({ queryKey: ["applications"] });
      const previous = queryClient.getQueryData<typeof applications>(["applications"]);
      queryClient.setQueryData<typeof applications>(["applications"], (old = []) =>
        old.map((app: any) => (app.id === id ? { ...app, status: toStatus } : app))
      );
      return { previous };
    },
    onError: (_err, _vars, context: any) => {
      // Roll back
      queryClient.setQueryData(["applications"], context?.previous);
      toast.error("Invalid status transition. That move isn't allowed.");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
    },
  });

  const createMutation = useMutation({
    mutationFn: (jobId: string) => createApplication(jobId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["applications"] });
      setAddOpen(false);
      setSelectedJobId("");
      toast.success("Application added to board");
    },
    onError: (err: any) => {
      toast.error(err.message || "Failed to create application");
    },
  });

  // Group applications by status
  const applicationsByStatus: Record<string, typeof applications> = {};
  STATUS_COLUMNS.forEach((status) => {
    applicationsByStatus[status] = applications.filter((app: any) => app.status === status);
  });

  const handleDragStart = (e: React.DragEvent, appId: string) => {
    e.dataTransfer.setData("applicationId", appId);
  };

  const handleDrop = (e: React.DragEvent, newStatus: string) => {
    e.preventDefault();
    const appId = e.dataTransfer.getData("applicationId");
    if (appId) {
      transitionMutation.mutate({ id: appId, toStatus: newStatus });
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  if (isLoading) {
    return (
      <PageBody>
        <PageHeader eyebrow="Pipeline" title="Applications board" />
        <div className="grid place-items-center py-20">Loading...</div>
      </PageBody>
    );
  }

  const followupCount = followups.length;

  return (
    <PageBody>
      {/* Add Application Dialog */}
      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add application</DialogTitle>
            <DialogDescription>
              Choose a job you've already imported to track as an application.
            </DialogDescription>
          </DialogHeader>
          <div className="max-h-72 overflow-y-auto space-y-1 border rounded-md p-2">
            {jobsLoading ? (
              <div className="p-4 text-sm text-muted-foreground">Loading jobs…</div>
            ) : jobs.length === 0 ? (
              <div className="p-4 text-sm text-muted-foreground">
                No jobs imported yet.{" "}
                <Link to="/jobs/import" className="underline" onClick={() => setAddOpen(false)}>
                  Import jobs first →
                </Link>
              </div>
            ) : (
              jobs.map((job: any) => (
                <button
                  key={job.id}
                  onClick={() => setSelectedJobId(job.id)}
                  className={`w-full rounded border p-2.5 text-left text-xs transition-colors hover:bg-muted/40 ${
                    selectedJobId === job.id
                      ? "border-[color:var(--brand)] bg-[color:var(--brand)]/5 font-medium"
                      : "border-border"
                  }`}
                >
                  <span className="font-medium">{job.company}</span>
                  <span className="ml-2 text-muted-foreground">{job.title}</span>
                </button>
              ))
            )}
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setAddOpen(false)}>
              Cancel
            </Button>
            <Button
              disabled={!selectedJobId || createMutation.isPending}
              onClick={() => createMutation.mutate(selectedJobId)}
            >
              {createMutation.isPending ? "Adding…" : "Add application"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <PageHeader
        eyebrow="Pipeline"
        title="Applications board"
        description="Drag through the hiring lifecycle. Status transitions are deterministic - no AI auto-moves."
        actions={
          <>
            <Button variant="outline" size="sm" onClick={() => setAddOpen(true)}>
              + Add application
            </Button>
            <Link
              to="/applications/timeline"
              className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted"
            >
              Timeline view
            </Link>
            <Link
              to="/applications/followups"
              className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground hover:bg-foreground/90"
            >
              Follow-ups{followupCount > 0 ? ` · ${followupCount}` : ""}
            </Link>
          </>
        }
      />
      <div className="flex gap-4 overflow-x-auto pb-4">
        {STATUS_COLUMNS.map((col) => {
          const items = applicationsByStatus[col] || [];
          return (
            <div
              key={col}
              className="flex w-72 shrink-0 flex-col gap-2"
              onDrop={(e) => handleDrop(e, col)}
              onDragOver={handleDragOver}
            >
              <div className="flex items-center justify-between rounded-md bg-muted/40 px-3 py-1.5">
                <StatusPill status={col} />
                <span className="font-mono text-[11px] font-semibold tabular-nums text-muted-foreground">
                  {items.length}
                </span>
              </div>
              <div className="flex flex-col gap-2">
                {items.length === 0 ? (
                  <div className="grid h-20 place-items-center rounded-md border border-dashed border-border bg-muted/20 font-mono text-[10px] text-muted-foreground">
                    empty
                  </div>
                ) : (
                  items.map((app: any) => (
                    <Link
                      key={app.id}
                      to="/applications/$id"
                      params={{ id: app.id }}
                      className="space-y-1.5 rounded-md bg-card p-3 ring-1 ring-border hover:ring-[color:var(--brand)]/40"
                      draggable
                      onDragStart={(e) => handleDragStart(e, app.id)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="text-[13px] font-semibold">
                          {app.job?.company || "Unknown"}
                        </div>
                        {app.score && <ScorePill value={app.score} />}
                      </div>
                      <div className="text-[11px] text-muted-foreground">
                        {app.job?.title || "Unknown"}
                      </div>
                      {app.general_notes ? (
                        <div className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium text-foreground/80">
                          {app.general_notes}
                        </div>
                      ) : null}
                      <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                        <span>{new Date(app.created_at).toLocaleDateString()}</span>
                      </div>
                    </Link>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
      <Panel title="Board legend">
        <div className="flex flex-wrap gap-3 px-4 py-3 text-[11px] text-muted-foreground">
          {STATUS_COLUMNS.map((s) => (
            <StatusPill key={s} status={s} />
          ))}
        </div>
      </Panel>
    </PageBody>
  );
}
