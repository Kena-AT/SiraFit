import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, ScorePill, StatusPill } from "@/components/sirafit/bits";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getApplications, transitionApplicationStatus } from "@/lib/api/applications";
import { useState } from "react";

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
  const { data: applications = [], isLoading } = useQuery({
    queryKey: ["applications"],
    queryFn: getApplications,
  });

  const transitionMutation = useMutation({
    mutationFn: ({ id, toStatus }: { id: string; toStatus: string }) =>
      transitionApplicationStatus(id, toStatus),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["applications"] }),
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

  return (
    <PageBody>
      <PageHeader
        eyebrow="Pipeline"
        title="Applications board"
        description="Drag through the hiring lifecycle. Status transitions are deterministic — no AI auto-moves."
        actions={
          <>
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
              Follow-ups · 4
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
                  items.map((app: any, i: number) => (
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
